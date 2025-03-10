import logging
from typing import List, Set, Tuple

import requests
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


def defillama_name_to_slug(name: str) -> str:
    """
    Convert a protocol name back to a defillama slug, reversing the
    transformations done by defillama_slug_to_name.

    Args:
        name (str): The protocol name to convert.

    Returns:
        str: The original defillama slug
    """

    if name.endswith("_protocol"):
        name = name[:-9]

    return name.replace("__dot__", ".").replace("_", "-")


def mk_defillama_config(urls: List[str]) -> RESTAPIConfig:
    """
    Create a REST API config for fetching defillama data.

    Args:
        urls (Set[str]): A set of defillama urls to fetch.

    Returns:
        RESTAPIConfig: The REST API config.
    """

    return {
        "client": {
            "base_url": "https://api.llama.fi/",
        },
        "resource_defaults": {
            "primary_key": "id",
            "write_disposition": "merge",
        },
        "resources": list(
            map(
                lambda protocol: {
                    "name": defillama_slug_to_name(protocol),
                    "endpoint": {
                        "path": f"protocol/{protocol}",
                        "data_selector": "$",
                    },
                },
                urls,
            )
        ),
    }


def filter_valid_slugs(slugs: Set[str]) -> Set[str]:
    """
    Filter out invalid defillama slugs from a set of slugs.

    Args:
        slugs (Set[str]): The set of slugs to filter.

    Returns:
        Set[str]: The set of valid slugs.
    """

    for slug in slugs:
        try:
            r = requests.head(f"https://api.llama.fi/protocol/{slug}", timeout=10)
            if r.status_code != 200:
                logger.warning(
                    f"Skipping invalid Defillama slug '{slug}': {r.status_code} {r.text}"
                )
                slugs.remove(slug)
        except requests.Timeout:
            logger.warning(
                f"Timeout fetching '{slug}', it is likely valid but slow, keeping it"
            )
        except Exception as e:
            logger.warning(f"Skipping '{slug}' due to exception: {e})")
            slugs.remove(slug)

    return slugs


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


def fetch_defillama_protocols() -> Tuple[List[str], List[str]]:
    """
    Fetch defillama protocols from the ossd projects and the op_atlas dataset.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing the list of all defillama
        protocols and the list of defillama protocols that are present in the
        BigQuery dataset.
    """

    # NOTE: This project id must match the GCP project id in
    # `warehouse/metrics_tools/local/utils.py` so that it fetches the
    # same datasets and it does not cause any mismatch when running
    # `oso local initialize` and `oso local sqlmesh plan dev`.
    client = bigquery.Client(project="opensource-observer")

    op_atlas_query = """
        SELECT
            DISTINCT value
        FROM
            `opensource-observer.op_atlas.project__defi_llama_slug`
    """

    dataset = client.dataset("defillama_tvl")

    try:
        op_atlas_data = [row["value"] for row in client.query(op_atlas_query).result()]

        tables = [
            defillama_name_to_slug(table.table_id)
            for table in client.list_tables(dataset)
        ]
        fallback = False
    except Forbidden as e:
        logging.warning(f"Failed to fetch data from BigQuery, using fallback: {e}")

        op_atlas_data = []

        # NOTE: These tables are present on the `opensource-observer.defillama_tvl`
        # BigQuery dataset. They're a fallback in case the tables cannot be
        # fetched from BigQuery. Useful for CI/CD pipelines to test validity
        # of the defillama assets.
        # This will fail if the tables are not present in the BigQuery dataset.
        tables = ["optimism-bridge", "sushiswap"]
        fallback = True

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

    if fallback:
        ossd_defillama_parsed_urls.update(tables)

    ossd_defillama_parsed_urls = filter_valid_slugs(ossd_defillama_parsed_urls)

    return list(ossd_defillama_parsed_urls), list(
        ossd_defillama_parsed_urls.intersection(tables)
    )


# NOTE: SQLMesh depends on BigQuery to create the source tables for staging DefiLlama
# models. If these models are not present on BigQuery, SQLMesh will fail to
# create the source tables. By filtering out the protocols that are not present
# in BigQuery, we ensure that SQLMesh can create the source tables for the
# DefiLlama models.
# `ALL_DEFILLAMA_PROTOCOLS`: All DefiLlama protocols that are present in the
# OSSD projects and the op_atlas dataset.
# `DEFILLAMA_PROTOCOLS`: Only DefiLlama protocols that are present in the BigQuery
# dataset, filtered from ALL_DEFILLAMA_PROTOCOLS.
ALL_DEFILLAMA_PROTOCOLS, DEFILLAMA_PROTOCOLS = fetch_defillama_protocols()


def build_defillama_assets() -> List[AssetFactoryResponse]:
    """
    Creates a defillama asset factory configured to fetch defillama data
    given the current ossd projects with defillama urls. Also fetches
    defillama urls from the op_atlas dataset.

    Returns:
        AssetFactoryResponse: The defillama asset factory.
    """

    dlt_assets = create_rest_factory_asset(
        config=mk_defillama_config(ALL_DEFILLAMA_PROTOCOLS),
    )

    assets = dlt_assets(
        key_prefix=["defillama", "tvl"],
        op_tags={
            "dagster/concurrency_key": "defillama_tvl",
        },
        pool="defillama_tvl",
    )

    return assets


defillama_assets = build_defillama_assets()
