from dlt.sources.rest_api.typing import RESTAPIConfig

from ..factories.rest import create_rest_factory_asset


def defillama_slug_to_name(slug: str) -> str:
    return f"{slug.replace('-', '_').replace(".", '__dot__')}_protocol"


DEFILLAMA_PROTOCOLS = [
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "optimism-bridge",
    "dforce",
    "alchemix",
    "toros",
    "idle",
    "clusters",
    "lets-get-hai",
    "beefy",
    "ionic-protocol",
    "pyth-network",
    "tlx-finance",
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
                "name": defillama_slug_to_name(protocol),
                "endpoint": {
                    "path": f"protocol/{protocol}",
                    "data_selector": "$",
                },
            },
            DEFILLAMA_PROTOCOLS,
        )
    ),
}


dlt_assets = create_rest_factory_asset(
    config=config,
)

defillama_tvl_assets = dlt_assets(
    key_prefix=["defillama", "tvl"],
)
