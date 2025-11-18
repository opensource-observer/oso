from dagster import AssetExecutionContext
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from oso_dagster.factories import dlt_factory

metrics = [
    "daa",  # Daily Active Addresses
    "fdv",  # Fully Diluted Valuation
    "fees",  # Fees Paid by Users
    "market_cap",  # Market Cap
    "profit",  # Onchain Profit
    "rent_paid",  # Rent Paid to L1
    "stables_mcap",  # Stablecoin Market Cap
    "throughput",  # Throughput
    "tvl",  # Total Value Secured
    "txcosts",  # Median Transaction Costs
    "txcount",  # Transaction Count
]

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.growthepie.com/v1",
    },
    "resource_defaults": {
        "write_disposition": "replace",
    },
    "resources": [
        {
            "name": metric,
            "endpoint": {
                "path": f"export/{metric}.json",
                "data_selector": "$",
            },
        }
        for metric in metrics
    ],
}


@dlt_factory(
    key_prefix="growthepie",
    name="fundamentals",
    log_intermediate_results=True,
)
def growthepie_assets(context: AssetExecutionContext):
    """
    Asset that combines all growthepie metrics into a single table.
    """
    resources = rest_api_resources(config)

    # Set all resources to use the same table name so they union into one table
    for resource in resources:
        context.log.info(f"Processing metric: {resource.name}")
        resource.table_name = "fundamentals_full"

    yield from resources
