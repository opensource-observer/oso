import logging
from typing import Any, Dict, Generator, Set

import dlt
import pandas as pd
import requests
from dagster import AssetExecutionContext, ResourceParam
from dlt.destinations.adapters import bigquery_adapter
from dlt.sources.helpers.requests import Session
from google.api_core.exceptions import Forbidden
from google.cloud import bigquery
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory
from ossdirectory import fetch_data

logger = logging.getLogger(__name__)

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
    "bedrock-unibtc",
    "bedrock-brbtc",
    "bedrock-unieth",
    "bedrock-uniiotx",
    "beefy",
    "blueshift",
    "bmx",
    "bmx-classic-perps",
    "bmx-freestyle",
    "bmx-classic-amm",
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
    "mint-club-v1",
    "mint-club-v2",
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
    "sablier-lockup",
    "sablier-legacy",
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
    "swapmode-v2",
    "swapmode-v3",
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

DEFILLAMA_PROTOCOLS = ["aave", "sushiswap"]

DEFILLAMA_TVL_EPOCH = "2021-10-01T00:00:00.000Z"

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
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


def get_valid_defillama_slugs() -> Set[str]:
    """
    Get all valid defillama slugs from the ossd projects and the op_atlas dataset.

    Returns:
        Set[str]: A set of valid defillama slugs.
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

    try:
        r = requests.get(
            "https://api.llama.fi/protocols",
            timeout=10,
        )
        r.raise_for_status()

        valid_defillama_slugs = {x["slug"] for x in r.json()}
        return valid_defillama_slugs | ossd_defillama_parsed_urls
    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to fetch Defillama protocols: {e}")
        return ossd_defillama_parsed_urls


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


def parse_chain_tvl(
    protocol: str,
    parent_protocol: str,
    chain_tvls_raw: Dict,
) -> Generator[Dict[str, Any], None, None]:
    """
    Extract aggregated TVL events from the chainTvls field.
    For each chain, each event is expected to have a date and a totalLiquidityUSD value.

    Args:
        protocol (str): The protocol slug
        parent_protocol (str): The parent protocol (if any)
        chain_tvls_raw (Dict): The raw chain TVL data

    Yields:
        Dict[str, Any]: Individual TVL events
    """
    chains = chain_tvls_raw.keys()
    for chain in chains:
        if (
            not isinstance(chain_tvls_raw[chain], dict)
            or "tvl" not in chain_tvls_raw[chain]
        ):
            continue

        tvl_history = chain_tvls_raw[chain]["tvl"]
        if not tvl_history:
            continue

        for entry in tvl_history:
            try:
                timestamp = pd.Timestamp(entry["date"], unit="s")
                amount = float(entry["totalLiquidityUSD"])

                event = {
                    "time": timestamp.isoformat(),
                    "slug": protocol,
                    "protocol": protocol,
                    "parent_protocol": parent_protocol,
                    "chain": defillama_chain_mappings(chain),
                    "token": "USD",
                    "tvl": amount,
                    "event_type": "TVL",
                }
                yield event
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing TVL entry for {protocol}/{chain}: {e}")
                continue


def get_defillama_tvl_events(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch DefiLlama protocol TVL data for all available dates.

    Args:
        context (AssetExecutionContext): The execution context

    Yields:
        Dict[str, Any]: Individual TVL events for all protocols and chains
    """
    session = Session(timeout=300)

    context.log.info("Processing all TVL data")

    valid_slugs = get_valid_defillama_slugs()
    context.log.info(f"Found {len(valid_slugs)} valid DefiLlama protocols")

    for i, slug in enumerate(valid_slugs):
        try:
            url = f"https://api.llama.fi/protocol/{slug}"
            context.log.info(
                f"Fetching data for protocol: {slug} ({i + 1}/{len(valid_slugs)})"
            )

            response = session.get(url)
            response.raise_for_status()
            protocol_data = response.json()

            parent_protocol = ""
            if "parentProtocol" in protocol_data:
                parent_protocol = protocol_data.get("parentProtocol", "")

            if "chainTvls" in protocol_data:
                yield from parse_chain_tvl(
                    slug,
                    parent_protocol,
                    protocol_data["chainTvls"],
                )

        except requests.exceptions.RequestException as e:
            context.log.warning(f"Failed to fetch data for protocol {slug}: {e}")
            continue
        except Exception as e:
            context.log.error(f"Error processing protocol {slug}: {e}")
            continue


@dlt_factory(
    key_prefix="defillama",
    name="tvl_events",
    op_tags={
        "dagster/concurrency_key": "defillama_tvl",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def defillama_tvl_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Create and register a Dagster asset that materializes DeFiLlama TVL data.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        global_config (DagsterConfig): Global configuration parameters.

    Yields:
        Generator: A generator that yields DeFiLlama TVL events.
    """
    resource = dlt.resource(
        get_defillama_tvl_events(context),
        name="tvl_events",
        primary_key=["slug", "chain", "time"],
        write_disposition="replace",
    )

    if global_config.enable_bigquery:
        bigquery_adapter(
            resource,
            partition="time",
            cluster=[
                "slug",
                "chain",
            ],
        )

    yield resource
