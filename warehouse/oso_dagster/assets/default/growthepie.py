from dlt.sources.rest_api.typing import RESTAPIConfig
from oso_dagster.factories.rest import create_rest_factory_asset

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.growthepie.com/v1",
    },
    "resource_defaults": {
        "write_disposition": "replace",
    },
    "resources": [
        {
            "name": "fundamentals",
            "endpoint": {
                "path": "fundamentals.json",
                "data_selector": "$",
            },
        }
    ],
}

dlt_assets = create_rest_factory_asset(
    config=config,
)

growthepie_assets = dlt_assets(
    key_prefix="growthepie",
    name="fundamentals",
)
