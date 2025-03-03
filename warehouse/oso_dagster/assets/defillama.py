from dlt.sources.rest_api.typing import RESTAPIConfig

from ..factories.rest import create_rest_factory_asset

DEFILLAMA_PROTOCOLS = [
    "aave",
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "across",
    "acryptos",
    "aera",
    "aerodrome-slipstream",
    "aerodrome-v1",
    "aktionariat",
    "alchemix",
    "alien-base-v2",
    "alien-base-v3",
    "amped-finance",
    "arcadia-v2",
    "aura",
    "avantis",
    "bakerfi",
    "balancer-v2",
    "balancer-v3",
    "baseswap",
    "baseswap-v2",
    "bedrock",
    "beefy",
    "blueshift",
    "bmx",
    "bsx-exchange",
    "clusters",
    "compound-v3",
    "contango-v2",
    "curve-dex",
    "dackieswap",
    "derive-v1",
    "derive-v2",
    "dforce",
    "dhedge",
    "exactly",
    "extra-finance-leverage-farming",
    "gains-network",
    "harvest-finance",
    "hermes-v2",
    "hop-protocol",
    "idle",
    "infinitypools",
    "intentx",
    "ionic-protocol",
    "javsphere",
    "jumper-exchange",
    "kelp",
    "kim-exchange-v3",
    "kromatika",
    "krystal",
    "lets-get-hai",
    "lombard-vault",
    "meme-wallet",
    "meson",
    "mint-club",
    "mintswap-finance",
    "moonwell",
    "morpho",
    "morpho-blue",
    "mux-perps",
    "okx",
    "optimism-bridge",
    "origin-protocol",
    "overnight-finance",
    "pancakeswap-amm-v3",
    "pendle",
    "perpetual-protocol",
    "pinto",
    "polynomial-trade",
    "pooltogether-v5",
    "pyth-network",
    "rainbow",
    "renzo",
    "reserve-protocol",
    "sablier",
    "seamless-protocol",
    "silo-v1",
    "solidly-v3",
    "sommelier",
    "sonus-exchange",
    "sonus-exchange-amm",
    "sonus-exchange-clmm",
    "stargate-v1",
    "stargate-v2",
    "superswap-ink",
    "sushi",
    "sushiswap",
    "sushiswap-v3",
    "swapbased",
    "swapbased-amm",
    "swapbased-concentrated-liquidity",
    "swapbased-perp",
    "swapmode",
    "synapse",
    "synfutures-v3",
    "synthetix",
    "synthetix-v3",
    "tarot",
    "team-finance",
    "tlx-finance",
    "toros",
    "velodrome-v2",
    "woo-x",
    "woofi",
    "woofi-earn",
    "yearn-finance",
    "zerolend"
]


def defillama_slug_to_name(slug: str) -> str:
    return f"{slug.replace('-', '_').replace(".", '__dot__')}_protocol"


def defillama_chain_mappings(chain: str) -> str:
    chain = chain.lower()
    return {
        "arbitrum": "arbitrum_one",
        "ethereum": "mainnet",
        "fraxtal": "frax",
        "op mainnet": "optimism",
        "polygon": "matic",
        "polygon zkevm": "polygon_zkevm",
        "swellchain": "swell",
        "world chain": "worldchain",
        "zksync era": "zksync_era",
    }.get(chain, chain)


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
