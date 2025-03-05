from typing import List, Set

from dlt.sources.rest_api.typing import RESTAPIConfig
from ossdirectory import fetch_data

from ..factories import AssetFactoryResponse
from ..factories.rest import create_rest_factory_asset

LEGACY_DEFILLAMA_PROTOCOLS = [
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
    # "pancakeswap-amm-v3",  # continuously fails
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
    "zerolend",
]


def defillama_slug_to_name(slug: str) -> str:
    """
    Parse a defillama slug into a protocol name, replacing dashes
    with underscores and periods with '__dot__'.

    Args:
        slug (str): The defillama slug to parse.

    Returns:
        str: The parsed protocol name
    """

    return f"{slug.replace('-', '_').replace(".", '__dot__')}_protocol"


def defillama_chain_mappings(chain: str) -> str:
    """
    Map defillama chains to their canonical names.

    Args:
        chain (str): The chain to map.

    Returns:
        str: The mapped chain or the original chain if no mapping is found.
    """

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


def mk_defillama_config(urls: Set[str]) -> RESTAPIConfig:
    """
    Create a REST API config for fetching defillama data.

    Args:
        urls (Set[str]): A set of defillama urls to fetch.

    Returns:
        RESTAPIConfig: The REST API config.
    """

    return {
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
                urls,
            )
        ),
    }


def extract_protocol(url: str) -> str:
    """
    Extract the protocol name from a defillama url. It is assumed that
    the protocol name is the last part of the url. For example, in the
    url "https://defillama.com/protocol/gyroscope-protocol", the protocol name
    is "gyroscope-protocol".

    Args:
        url (str): The defillama url to parse.

    Returns:
        str: The protocol name.
    """

    return url.split("/")[-1]


def build_defillama_assets() -> List[AssetFactoryResponse]:
    """
    Creates a defillama asset factory configured to fetch defillama data
    given the current ossd projects with defillama urls.

    Args:
        cbt (CBTResource): The BigQuery resource.

    Returns:
        AssetFactoryResponse: The defillama asset factory.
    """

    ossd_data = fetch_data()

    ossd_defillama_raw_urls = [
        value["url"]
        for entry in ossd_data.projects
        if entry.get("defillama")
        for value in entry["defillama"]
    ]

    ossd_defillama_parsed_urls = set(
        extract_protocol(url) for url in ossd_defillama_raw_urls
    )

    ossd_defillama_parsed_urls.update(LEGACY_DEFILLAMA_PROTOCOLS)

    dlt_assets = create_rest_factory_asset(
        config=mk_defillama_config(ossd_defillama_parsed_urls),
    )

    assets = dlt_assets(
        key_prefix=["defillama", "tvl"],
    )

    return assets


defillama_assets = build_defillama_assets()
