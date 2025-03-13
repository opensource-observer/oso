"""Constants used to determine the start date for incremental data collection."""

from metrics_tools.utils.env import coalesce_str


def coalesce_start_value(var_name: str, default: str) -> str:
    return coalesce_str(
        ["SQLMESH_DEBUG_START", f"SQLMESH_DEBUG_{var_name.upper()}_START"], default
    )


blockchain_incremental_start = coalesce_start_value("BLOCKCHAIN", "2021-10-01")
github_incremental_start = coalesce_start_value("GITHUB", "2015-01-01")
funding_incremental_start = coalesce_start_value("FUNDING", "2015-01-01")
defillama_incremental_start = coalesce_start_value("DEFILLAMA", "2021-10-01")
