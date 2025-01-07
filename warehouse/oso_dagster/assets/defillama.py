from dlt.sources.rest_api.typing import RESTAPIConfig

from ..factories.rest import create_rest_factory_asset

DEFI_LLAMA_PROTOCOLS = [
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "optimism-bridge",
    # Old protocols...
    "ether.fi",
    "compound-finance",
    "dforce",
    "alchemix",
    "toros",
    "lisk",
    "idle",
    "derive",
    "contango",
    "clusters",
    "kelp-dao",
    "lets-get-hai",
    "beefy",
    "ionic-protocol",
    "resolv",
    "pyth-network",
    "kroma",
    "tlx-finance",
    "uniswap",
    "velodrome",
    "origin",
    "origin-protocol",
    "polynomial-protocol",
    "extra-finance",
    "frax-finance",
    "mode",
    "renzo",
]


config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.llama.fi/",
    },
    "resource_defaults": {
        "primary_key": "id",
        "write_disposition": "merge",
    },
    "resources": list(
        map(
            lambda protocol: {
                "name": f"{protocol.replace('-', '_').replace(".", '__dot__')}_protocol",
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
