import logging
from typing import Any, Dict, Generator, List, Set

import dlt
import requests
from dlt.sources.helpers.requests import Session
from dlt.sources.rest_api.typing import RESTAPIConfig
from google.api_core.exceptions import Forbidden
from google.cloud import bigquery
from ossdirectory import fetch_data

from ..factories import AssetFactoryResponse
from ..factories.rest import create_rest_factory_asset

logger = logging.getLogger(__name__)

# These protocols cause issues with dlt and its decoding
# implementation. It is not trivial to fix these issues
# so we disable them for now. For more info, see #3163.
# TODO(jabolo): Fix these issues and re-enable these protocols.
DISABLED_DEFILLAMA_PROTOCOLS = [
    "pancakeswap-amm-v3",
    "hermes-v2",
    "sakefinance",
    "jumper-exchange",
    "uniswap-v2",
    "uniswap-v3",
    "extra-finance-leverage-farming",
]

LEGACY_DEFILLAMA_PROTOCOLS = [
    "aave",
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "across",
    "acryptos",
    "aera",
    "aerodrome-slipstream",
    "aerodrome-v1",
    "aktionariat",
    "alchemix",
    "alien-base-v2",
    "alien-base-v3",
    "amped-finance",
    "arcadia-v2",
    "aura",
    "avantis",
    "bakerfi",
    "balancer-v2",
    "balancer-v3",
    "baseswap",
    "baseswap-v2",
    "bedrock",
    "beefy",
    "blueshift",
    "bmx",
    "bsx-exchange",
    "clusters",
    "compound-v3",
    "contango-v2",
    "curve-dex",
    "dackieswap",
    "derive-v1",
    "derive-v2",
    "dforce",
    "dhedge",
    "exactly",
    "extra-finance-leverage-farming",
    "gains-network",
    "harvest-finance",
    "hermes-v2",
    "hop-protocol",
    "idle",
    "infinitypools",
    "intentx",
    "ionic-protocol",
    "javsphere",
    "jumper-exchange",
    "kelp",
    "kim-exchange-v3",
    "kromatika",
    "krystal",
    "lets-get-hai",
    "lombard-vault",
    "meme-wallet",
    "meson",
    "mint-club",
    "mintswap-finance",
    "moonwell",
    "morpho",
    "morpho-blue",
    "mux-perps",
    "okx",
    "optimism-bridge",
    "origin-protocol",
    "overnight-finance",
    "pendle",
    "perpetual-protocol",
    "pinto",
    "polynomial-trade",
    "pooltogether-v5",
    "pyth-network",
    "rainbow",
    "renzo",
    "reserve-protocol",
    "sablier",
    "seamless-protocol",
    "silo-v1",
    "solidly-v3",
    "sommelier",
    "sonus-exchange",
    "sonus-exchange-amm",
    "sonus-exchange-clmm",
    "stargate-v1",
    "stargate-v2",
    "superswap-ink",
    "sushi",
    "sushiswap",
    "sushiswap-v3",
    "swapbased",
    "swapbased-amm",
    "swapbased-concentrated-liquidity",
    "swapbased-perp",
    "swapmode",
    "synapse",
    "synfutures-v3",
    "synthetix",
    "synthetix-v3",
    "tarot",
    "team-finance",
    "tlx-finance",
    "toros",
    "velodrome-v2",
    "woo-x",
    "woofi",
    "woofi-earn",
    "yearn-finance",
    "zerolend",
]

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "3584Mi"},
        },
    },
}


def defillama_slug_to_name(slug: str) -> str:
    """
    Parse a defillama slug into a protocol name, replacing dashes
    with underscores and periods with '__dot__'.

    Args:
        slug (str): The defillama slug to parse.

    Returns:
        str: The parsed protocol name
    """

    return f"{slug.replace('-', '_').replace(".", '__dot__')}_protocol"


def defillama_chain_mappings(chain: str) -> str:
    """
    Map defillama chains to their canonical names.

    Args:
        chain (str): The chain to map.

    Returns:
        str: The mapped chain or the original chain if no mapping is found.
    """

    chain = chain.lower()
    return {
        "arbitrum": "arbitrum_one",
        "ethereum": "mainnet",
        "fraxtal": "frax",
        "op mainnet": "optimism",
        "polygon": "matic",
        "polygon zkevm": "polygon_zkevm",
        "swellchain": "swell",
        "world chain": "worldchain",
        "zksync era": "zksync_era",
    }.get(chain, chain)


def filter_valid_slugs(slugs: Set[str]) -> Set[str]:
    """
    Filter out invalid defillama slugs from a set of slugs.

    Args:
        slugs (Set[str]): The set of slugs to filter.

    Returns:
        Set[str]: The set of valid slugs.
    """

    all_slugs = set(slugs)

    try:
        r = requests.get("https://api.llama.fi/protocols", timeout=5)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch Defillama protocols: {e}")
        return all_slugs

    valid_slugs = {x["slug"] for x in r.json()}
    return all_slugs.intersection(valid_slugs)


def extract_protocol(url: str) -> str:
    """
    Extract the protocol name from a defillama url. It is assumed that
    the protocol name is the last part of the url. For example, in the
    url "https://defillama.com/protocol/gyroscope-protocol", the protocol name
    is "gyroscope-protocol".

    Args:
        url (str): The defillama url to parse.

    Returns:
        str: The protocol name.
    """

    return url.split("/")[-1]


@dlt.resource(name="protocols")
def fetch_defillama_protocols() -> Generator[List[Dict[str, str]], None, None]:
    """
    Fetch all defillama protocols from the ossd projects and the op_atlas dataset.

    Returns:
        Generator[List[Dict[str, str]], None, None]: A generator yielding a list of
        dictionaries containing the protocol slugs.
    """

    client = bigquery.Client()

    op_atlas_query = """
        SELECT
            DISTINCT value
        FROM
            `opensource-observer.op_atlas.project__defi_llama_slug`
    """

    try:
        op_atlas_data = [row["value"] for row in client.query(op_atlas_query).result()]

    except Forbidden as e:
        logging.warning(f"Failed to fetch data from BigQuery, using fallback: {e}")

        op_atlas_data = []

    ossd_data = fetch_data()

    ossd_defillama_raw_urls = [
        value["url"]
        for entry in ossd_data.projects
        if entry.get("defillama")
        for value in entry["defillama"]
    ]

    ossd_defillama_parsed_urls = set(
        extract_protocol(url) for url in ossd_defillama_raw_urls
    )

    ossd_defillama_parsed_urls.update(op_atlas_data)
    ossd_defillama_parsed_urls.update(LEGACY_DEFILLAMA_PROTOCOLS)

    ossd_defillama_parsed_urls.difference_update(DISABLED_DEFILLAMA_PROTOCOLS)

    yield [{"name": slug} for slug in filter_valid_slugs(ossd_defillama_parsed_urls)]


def add_original_slug(record: Any) -> Any:
    """
    Add the original slug to the record.

    Args:
        record: The record to modify.

    Returns:
        The modified record.
    """

    record["slug"] = record.get("_protocols_name", "")
    del record["_protocols_name"]

    return record


def mk_defillama_config() -> RESTAPIConfig:
    """
    Create a REST API config for fetching defillama data.

    Returns:
        RESTAPIConfig: The REST API config.
    """

    return {
        "client": {
            "base_url": "https://api.llama.fi/",
            "session": Session(timeout=300),
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "replace",
            "parallelized": True,
            "max_table_nesting": 0,
            "table_name": "defillama/tvl",
        },
        "resources": [
            {
                "name": "slugs",
                "endpoint": {
                    "path": "protocol/{protocol}",
                    "data_selector": "$",
                    "params": {
                        "protocol": {
                            "type": "resolve",
                            "resource": "protocols",
                            "field": "name",
                        },
                    },
                },
                "include_from_parent": ["name"],
                "processing_steps": [
                    {"map": add_original_slug},  # type: ignore
                ],
            },
            fetch_defillama_protocols(),
        ],
    }


def build_defillama_assets() -> List[AssetFactoryResponse]:
    """
    Creates a defillama asset factory configured to fetch defillama data
    given the current ossd projects with defillama urls. Also fetches
    defillama urls from the op_atlas dataset.

    Returns:
        AssetFactoryResponse: The defillama asset factory.
    """

    dlt_assets = create_rest_factory_asset(
        config=mk_defillama_config(),
    )

    assets = dlt_assets(
        key_prefix="defillama",
        name="tvl",
        op_tags={
            "dagster/concurrency_key": "defillama_tvl",
            "dagster-k8s/config": K8S_CONFIG,
        },
        pool="defillama_tvl",
    )

    return assets


defillama_assets = build_defillama_assets()
