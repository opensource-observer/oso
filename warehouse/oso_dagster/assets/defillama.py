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


K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
        },
    },
}


def get_valid_defillama_chains() -> Set[str]:
    """
    Get all valid defillama chain identifiers from the defillama.chains table.
    """
    client = bigquery.Client()
    query = """
        SELECT DISTINCT name
        FROM `opensource-observer.defillama.chains`
    """

    chains = set()
    try:
        chains.update({row["name"] for row in client.query(query).result()})
    except Exception as e:
        context.log.warning(f"Failed to fetch valid Defillama chains: {e}")
    return chains


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

    try:
        r = requests.get(
            "https://api.llama.fi/protocols",
            timeout=10,
        )
        r.raise_for_status()

        valid_defillama_slugs = {x["slug"] for x in r.json()}
        return valid_defillama_slugs & ossd_defillama_parsed_urls
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
                if not isinstance(timestamp, pd.Timestamp) or pd.isna(timestamp):
                    continue
                amount = float(entry["totalLiquidityUSD"])

                event = {
                    "time": timestamp.isoformat(),
                    "slug": protocol,
                    "protocol": protocol,
                    "parent_protocol": parent_protocol,
                    "chain": chain,
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


def parse_timeseries_events(
    *,
    slug: str,
    parent_protocol: str,
    raw: list,
    event_type: str,
) -> Generator[Dict[str, Any], None, None]:
    """
    Parse and yield time series events from raw DefiLlama chart data.

    Args:
        slug (str): The slug identifying the protocol (e.g., "velodrome-v1").
        parent_protocol (str): The parent protocol name, if available.
        raw (list): A list of entries from a DefiLlama time series chart.
            Each entry is [timestamp, value], where `value` is either a number
            (for aggregated metrics) or a breakdown dict (by chain and source).
        event_type (str): A string label indicating the type of metric
            (e.g., "TRADING_VOLUME" or "LP_FEES").

    Yields:
        Dict[str, Any]: One parsed time series event per row with fields:
            - time (ISO string)
            - slug, protocol, parent_protocol
            - chain (if available)
            - token ("USD")
            - event_type
            - amount (float)
    """

    for ts, val in raw:
        try:
            dt = pd.Timestamp(ts, unit="s")
            if not isinstance(dt, pd.Timestamp) or pd.isna(dt):
                continue

            if isinstance(val, (int, float)):
                yield {
                    "time": dt.isoformat(),
                    "slug": slug,
                    "protocol": slug,
                    "parent_protocol": parent_protocol,
                    "chain": "",
                    "token": "USD",
                    "event_type": event_type,
                    "amount": float(val),
                }

            elif isinstance(val, dict):
                for chain, nested in val.items():
                    num = next(iter(nested.values()))
                    yield {
                        "time": dt.isoformat(),
                        "slug": slug,
                        "protocol": slug,
                        "parent_protocol": parent_protocol,
                        "chain": chain,
                        "token": "USD",
                        "event_type": event_type,
                        "amount": float(num),
                    }

        except Exception as e:
            logger.warning(f"{event_type}: could not parse {slug} entry {val}: {e}")


def get_defillama_volume_events(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch and yield daily trading volume events for all valid DefiLlama protocols.

    Args:
        context (AssetExecutionContext): The Dagster execution context used
            for logging and task coordination.

    Yields:
        Dict[str, Any]: Parsed trading volume entries with slug, time, amount,
        and other metadata fields.
    """

    session = Session(timeout=300)
    valid_slugs = get_valid_defillama_slugs()

    for i, slug in enumerate(valid_slugs):
        url = (
            f"https://api.llama.fi/summary/dexs/{slug}"
            "?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=false"
        )
        try:
            context.log.info(f"[Volumes] {i + 1}/{len(valid_slugs)} {slug}")
            r = session.get(url)
            r.raise_for_status()
            data = r.json()

            parent = data.get("parentProtocol", "")
            chart = data.get("totalDataChartBreakdown", data.get("totalDataChart", []))

            yield from parse_timeseries_events(
                slug=slug,
                parent_protocol=parent,
                raw=chart,
                event_type="TRADING_VOLUME",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                continue
            context.log.warning(f"Volumes: {slug}: {e}")
        except Exception as e:
            context.log.error(f"Volumes: {slug}: {e}")


@dlt_factory(
    key_prefix="defillama",
    name="trading_volume_events",
    op_tags={
        "dagster/concurrency_key": "defillama_volume",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def defillama_volume_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Dagster asset that extracts and loads daily trading volume data
    from DefiLlama into BigQuery via DLT.

    Args:
        context (AssetExecutionContext): The Dagster execution context.
        global_config (DagsterConfig): Global configuration values including BigQuery toggle.

    Yields:
        DLT resource: A DLT stream that materializes trading volume rows
        to the configured destination (e.g., BigQuery).
    """
    resource = dlt.resource(
        get_defillama_volume_events(context),
        name="trading_volume_events",
        primary_key=["slug", "chain", "time"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, partition="time", cluster=["slug", "chain"])
    yield resource


def get_defillama_fee_events(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch and yield daily liquidity provider (LP) fee events for all valid DefiLlama protocols.

    Args:
        context (AssetExecutionContext): The Dagster execution context used
            for logging and task coordination.

    Yields:
        Dict[str, Any]: Parsed LP fee entries with slug, time, amount,
        and other metadata fields.
    """

    session = Session(timeout=300)
    valid_slugs = get_valid_defillama_slugs()

    for i, slug in enumerate(valid_slugs):
        url = f"https://api.llama.fi/summary/fees/{slug}?dataType=dailyFees"
        try:
            context.log.info(f"[Fees] {i + 1}/{len(valid_slugs)} {slug}")
            r = session.get(url)
            r.raise_for_status()
            data = r.json()

            parent = data.get("parentProtocol", "")
            chart = data.get("totalDataChartBreakdown", data.get("totalDataChart", []))

            yield from parse_timeseries_events(
                slug=slug,
                parent_protocol=parent,
                raw=chart,
                event_type="LP_FEES",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                continue
            context.log.warning(f"LP Fees: {slug}: {e}")
        except Exception as e:
            context.log.error(f"LP Fees: {slug}: {e}")


@dlt_factory(
    key_prefix="defillama",
    name="lp_fee_events",
    op_tags={
        "dagster/concurrency_key": "defillama_fees",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def defillama_fee_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Dagster asset that extracts and loads daily LP fee data
    from DefiLlama into BigQuery via DLT.

    Args:
        context (AssetExecutionContext): The Dagster execution context.
        global_config (DagsterConfig): Global configuration values including BigQuery toggle.

    Yields:
        DLT resource: A DLT stream that materializes LP fee rows
        to the configured destination (e.g., BigQuery).
    """

    resource = dlt.resource(
        get_defillama_fee_events(context),
        name="lp_fee_events",
        primary_key=["slug", "chain", "time"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, partition="time", cluster=["slug", "chain"])
    yield resource


def get_defillama_protocol_metadata(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch protocol metadata from the DefiLlama API.

    Args:
        context (AssetExecutionContext): The Dagster execution context used
            for logging and task coordination.

    Yields:
        Dict[str, Any]: Protocol metadata entries with fields like id, name,
        address, symbol, url, description, logo, chain, category, twitter,
        parentProtocol, and slug.
    """
    session = Session(timeout=300)

    try:
        context.log.info("Fetching protocol metadata from DefiLlama")
        response = session.get("https://api.llama.fi/protocols")
        response.raise_for_status()
        protocols = response.json()

        for protocol in protocols:
            yield {
                "id": str(protocol.get("id", "")),
                "slug": str(protocol.get("slug", "")),
                "name": str(protocol.get("name", "")),
                "address": str(protocol.get("address", "")),
                "symbol": str(protocol.get("symbol", "")),
                "url": str(protocol.get("url", "")),
                "description": str(protocol.get("description", "")),
                "logo": str(protocol.get("logo", "")),
                "chain": str(protocol.get("chain", "")),
                "category": str(protocol.get("category", "")),
                "twitter": str(protocol.get("twitter", "")),
                "parent_protocol": str(protocol.get("parentProtocol", "")),
            }

    except requests.exceptions.RequestException as e:
        context.log.error(f"Failed to fetch protocol metadata: {e}")
        raise


@dlt_factory(
    key_prefix="defillama",
    name="protocol_metadata",
    op_tags={
        "dagster/concurrency_key": "defillama_metadata",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def defillama_protocol_metadata_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Dagster asset that extracts and loads protocol metadata from DefiLlama
    into BigQuery via DLT.

    Args:
        context (AssetExecutionContext): The Dagster execution context.
        global_config (DagsterConfig): Global configuration values including BigQuery toggle.

    Yields:
        DLT resource: A DLT stream that materializes protocol metadata rows
        to the configured destination (e.g., BigQuery).
    """
    resource = dlt.resource(
        get_defillama_protocol_metadata(context),
        name="protocol_metadata",
        primary_key=["slug"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, cluster=["slug"])
    yield resource


def get_defillama_historical_chain_tvl(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch historical chain TVL data for specified chains from DefiLlama API.

    Args:
        context (AssetExecutionContext): The Dagster execution context used
            for logging and task coordination.

    Yields:
        Dict[str, Any]: Historical chain TVL entries with chain, time, and tvl fields.
    """
    session = Session(timeout=300)

    # Initial list of chains to fetch
    initial_chains = {
        "ethereum",
        "polygon",
        "arbitrum",
        "celo",
        "mint",
        "base",
        "optimism",
        "unichain",
    }
    valid_chains = get_valid_defillama_chains()
    chains = valid_chains if valid_chains else initial_chains

    for i, chain in enumerate(chains):
        try:
            url = f"https://api.llama.fi/v2/historicalChainTvl/{chain}"
            context.log.info(f"[Historical Chain TVL] {i + 1}/{len(chains)} {chain}")

            response = session.get(url)
            response.raise_for_status()
            data = response.json()

            # Parse the historical TVL data
            for entry in data:
                try:
                    timestamp = pd.Timestamp(entry["date"], unit="s")
                    if not isinstance(timestamp, pd.Timestamp) or pd.isna(timestamp):
                        continue

                    amount = float(entry["tvl"])

                    event = {
                        "time": timestamp.isoformat(),
                        "chain": chain,
                        "tvl": amount,
                    }
                    yield event

                except (KeyError, ValueError) as e:
                    context.log.warning(f"Error parsing TVL entry for {chain}: {e}")
                    continue

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                context.log.warning(f"Chain {chain} not found (404)")
                continue
            context.log.warning(f"Historical Chain TVL: {chain}: {e}")
        except Exception as e:
            context.log.error(f"Historical Chain TVL: {chain}: {e}")


@dlt_factory(
    key_prefix="defillama",
    name="historical_chain_tvl",
    op_tags={
        "dagster/concurrency_key": "defillama_historical_chain_tvl",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def defillama_historical_chain_tvl_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Dagster asset that extracts and loads historical chain TVL data
    from DefiLlama into BigQuery via DLT.

    Args:
        context (AssetExecutionContext): The Dagster execution context.
        global_config (DagsterConfig): Global configuration values including BigQuery toggle.

    Yields:
        DLT resource: A DLT stream that materializes historical chain TVL rows
        to the configured destination (e.g., BigQuery).
    """
    resource = dlt.resource(
        get_defillama_historical_chain_tvl(context),
        name="historical_chain_tvl",
        primary_key=["chain", "time"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, partition="time", cluster=["chain"])
    yield resource


def get_defillama_chains(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch chain data from the DefiLlama API.

    Args:
        context (AssetExecutionContext): The Dagster execution context used
            for logging and task coordination.

    Yields:
        Dict[str, Any]: Chain data entries with fields like gecko_id, tvl,
        tokenSymbol, cmcId, name, and chainId.
    """
    session = Session(timeout=300)

    try:
        context.log.info("Fetching chain data from DefiLlama")
        response = session.get("https://api.llama.fi/v2/chains")
        response.raise_for_status()
        chains = response.json()

        for chain in chains:
            yield {
                "gecko_id": chain.get("gecko_id", ""),
                "tvl": float(chain.get("tvl", 0.0)),
                "token_symbol": chain.get("tokenSymbol", ""),
                "cmc_id": chain.get("cmcId", ""),
                "name": chain.get("name", ""),
                "chain_id": int(chain["chainId"]) if chain.get("chainId") is not None else None,
            }

    except requests.exceptions.RequestException as e:
        context.log.error(f"Failed to fetch chain data: {e}")
        raise


@dlt_factory(
    key_prefix="defillama",
    name="chains",
    op_tags={
        "dagster/concurrency_key": "defillama_chains",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def defillama_chains_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Dagster asset that extracts and loads chain data from DefiLlama
    into BigQuery via DLT.

    Args:
        context (AssetExecutionContext): The Dagster execution context.
        global_config (DagsterConfig): Global configuration values including BigQuery toggle.

    Yields:
        DLT resource: A DLT stream that materializes chain data rows
        to the configured destination (e.g., BigQuery).
    """
    resource = dlt.resource(
        get_defillama_chains(context),
        name="chains",
        primary_key=["name"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, cluster=["name"])
    yield resource
