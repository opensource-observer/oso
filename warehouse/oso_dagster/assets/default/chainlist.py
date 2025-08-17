import logging
from typing import Any, Dict, Generator

import dlt
import requests
from dagster import AssetExecutionContext, ResourceParam
from dlt.destinations.adapters import bigquery_adapter
from dlt.sources.helpers.requests import Session
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory

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


def get_chainlist_data(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch chain data from Chainlist.org and yield individual chain records.

    Args:
        context (AssetExecutionContext): The execution context

    Yields:
        Dict[str, Any]: Individual chain records
    """
    session = Session(timeout=300)
    url = "https://chainlist.org/rpcs.json"

    try:
        context.log.info("Fetching chain data from Chainlist.org")
        response = session.get(url)
        response.raise_for_status()
        data = response.json()

        for chain in data:
            chain_info = {
                "name": chain.get("name"),
                "chain": chain.get("chain"),
                "chain_id": chain.get("chainId"),
                "network_id": chain.get("networkId"),
                "short_name": chain.get("shortName"),
                "chain_slug": chain.get("chainSlug"),
                "native_currency_name": chain.get("nativeCurrency", {}).get("name"),
                "native_currency_symbol": chain.get("nativeCurrency", {}).get("symbol"),
                "native_currency_decimals": chain.get("nativeCurrency", {}).get(
                    "decimals"
                ),
                "info_url": chain.get("infoURL"),
            }
            yield chain_info

    except requests.exceptions.RequestException as e:
        context.log.error(f"Failed to fetch data from Chainlist.org: {e}")
        raise
    except Exception as e:
        context.log.error(f"Error processing chain data: {e}")
        raise


@dlt_factory(
    key_prefix="chainlist",
    name="chains",
    op_tags={
        "dagster/concurrency_key": "chainlist_chains",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def chainlist_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Create and register a Dagster asset that materializes Chainlist chain data.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        global_config (DagsterConfig): Global configuration parameters.

    Yields:
        Generator: A generator that yields Chainlist chain records.
    """
    resource = dlt.resource(
        get_chainlist_data(context),
        name="chains",
        primary_key=["chain_id"],
        write_disposition="replace",
    )

    if global_config.gcp_bigquery_enabled:
        bigquery_adapter(
            resource,
            cluster=["chain_id", "chain"],
        )

    yield resource
