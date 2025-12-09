from dlt.sources.rest_api.typing import RESTAPIConfig
from oso_dagster.factories.rest import create_rest_factory_asset

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

FUNDAMENTALS_TABLE_NAME = "fundamentals_full"
FUNDAMENTALS_PRIMARY_KEY = ["metric_key", "origin_key", "date"]

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.growthepie.com/v1",
    },
    "resource_defaults": {
        "write_disposition": "replace",
        "table_name": FUNDAMENTALS_TABLE_NAME,
        "primary_key": FUNDAMENTALS_PRIMARY_KEY,
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


_growthepie_factory = create_rest_factory_asset(config=config)

growthepie_assets = _growthepie_factory(
    key_prefix="growthepie",
    name="fundamentals",
    log_intermediate_results=True,
    description="Asset that combines all GrowthePie metrics into a single fundamentals_full table.",
)
