import polars as pl
import requests
from dagster import asset


@asset(
    name="chains",
    description="Fetches chain data from Chainlist.org",
    group_name="chainlist",
)
def chainlist() -> pl.DataFrame:
    """
    Fetches chain data from Chainlist.org and returns them as a Polars DataFrame.
    Each row represents an RPC endpoint with its associated chain information.
    """
    url = "https://chainlist.org/rpcs.json"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
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
    return pl.DataFrame(flattened_data)
