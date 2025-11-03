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

dlt_assets = create_rest_factory_asset(
    config=config,
)

growthepie_assets = dlt_assets(
    key_prefix="growthepie",
    name="fundamentals",
)
