from dlt.sources.rest_api.typing import RESTAPIConfig

from ..factories.rest import create_rest_factory_asset

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.growthepie.xyz/v1",
    },
    "resource_defaults": {
        "write_disposition": "replace",
    },
    "resources": [
        {
            "name": "fundamentals_full",
            "endpoint": {
                "path": "fundamentals_full.json",
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
    name="growthepie",
)
