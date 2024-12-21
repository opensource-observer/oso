from dlt.sources.rest_api.typing import RESTAPIConfig

from ..factories.rest import create_rest_factory_asset

DEFI_LLAMA_PROTOCOLS = [
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "optimism-bridge",
    # ...
]


config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.llama.fi/",
    },
    "resources": list(
        map(
            lambda protocol: {
                "name": f"{protocol.replace('-', '_')}",
                "endpoint": {
                    "path": f"protocol/{protocol}",
                    "data_selector": "$",
                },
            },
            DEFI_LLAMA_PROTOCOLS,
        )
    ),
}

dlt_assets = create_rest_factory_asset(
    config=config,
)

defillama_tvl_assets = dlt_assets(
    key_prefix=["defillama", "tvl"],
)
