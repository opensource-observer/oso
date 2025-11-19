import dlt
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


@dlt.source(name="growthepie_fundamentals")
def growthepie_fundamentals_source():
    """
    Custom dlt source that wraps rest_api_resources and sets table_name
    at resource creation time to avoid undefined behavior.
    """
    resources = rest_api_resources(config)

    # Create new resources with the correct table name set at creation time
    def create_wrapped_resource(original_resource):
        """
        Factory function to create a wrapped resource with proper table_name.
        This avoids closure issues in the loop.
        """

        @dlt.resource(
            name=original_resource.name,
            table_name="fundamentals_full",
            write_disposition="replace",
        )
        def metric_resource():
            """
            Wrapper resource that yields data from the original resource
            with the table_name properly set at creation time.
            """
            yield from original_resource

        return metric_resource

    for resource in resources:
        yield create_wrapped_resource(resource)


@dlt_factory(
    key_prefix="growthepie",
    name="fundamentals",
    log_intermediate_results=True,
)
def growthepie_assets(context: AssetExecutionContext):
    """
    Asset that combines all growthepie metrics into a single table.
    Uses a custom dlt source that properly sets table_name at resource creation time
    instead of modifying resources after creation.
    """
    source = growthepie_fundamentals_source()
    for resource in source.resources.values():
        context.log.info(f"Processing metric: {resource.name}")
        yield resource
