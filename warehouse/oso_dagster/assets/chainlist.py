import polars as pl
import requests
from dagster import asset


@asset(
    name="chainlist_rpcs",
    description="Fetches RPC endpoints from Chainlist.org",
    group_name="chainlist",
)
def chainlist_rpcs() -> pl.DataFrame:
    """
    Fetches RPC endpoints from Chainlist.org and returns them as a Polars DataFrame.
    Each row represents an RPC endpoint with its associated chain information.
    """
    url = "https://chainlist.org/rpcs.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Flatten the nested structure
    flattened_data = []
    for chain in data:
        chain_info = {
            "name": chain.get("name"),
            "chain": chain.get("chain"),
            "chain_id": chain.get("chainId"),
            "network_id": chain.get("networkId"),
            "short_name": chain.get("shortName"),
            "chain_slug": chain.get("chainSlug"),
            "native_currency_name": chain.get("nativeCurrency", {}).get("name"),
            "native_currency_symbol": chain.get("nativeCurrency", {}).get("symbol"),
            "native_currency_decimals": chain.get("nativeCurrency", {}).get("decimals"),
            "info_url": chain.get("infoURL"),
        }

        # Add RPC endpoints
        for rpc in chain.get("rpc", []):
            rpc_data = chain_info.copy()
            rpc_data["rpc_url"] = rpc.get("url")
            rpc_data["rpc_tracking"] = rpc.get("tracking")
            rpc_data["rpc_is_open_source"] = rpc.get("isOpenSource")
            flattened_data.append(rpc_data)

        for explorer in chain.get("explorers", []):
            explorer_data = chain_info.copy()
            explorer_data["explorer_url"] = explorer.get("url")
            explorer_data["explorer_name"] = explorer.get("name")
            flattened_data.append(explorer_data)

    return pl.DataFrame(flattened_data)
