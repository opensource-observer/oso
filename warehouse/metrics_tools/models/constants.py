"""Constants used to determine the start date for incremental data collection."""

from metrics_tools.utils.env import coalesce_str, ensure_bool


def coalesce_start_value(var_name: str, default: str) -> str:
    return coalesce_str(
        ["SQLMESH_DEBUG_START", f"SQLMESH_DEBUG_{var_name.upper()}_START"], default
    )


superchain_audit_start = coalesce_str(["SQLMESH_DEBUG_START", "SQLMESH_DEBUG_SUPERCHAIN_AUDIT_START"], "2021-12-01")
# Generally this should always be set to now but if there are issues
# with the superchain data then this can be set to a specific date to
# avoid breaking the entire pipeline. That should only be used in
# extenuating circumstances.
superchain_audit_end = coalesce_str(["SQLMESH_DEBUG_SUPERCHAIN_AUDIT_END"], "2025-05-31")
#superchain_audit_end = coalesce_str(["SQLMESH_DEBUG_SUPERCHAIN_AUDIT_END"], "now")
blockchain_incremental_start = coalesce_start_value("BLOCKCHAIN", "2021-10-01")
deps_dev_incremental_start = coalesce_start_value("DEPS_DEV", "2015-01-01")
github_incremental_start = coalesce_start_value("GITHUB", "2015-01-01")
funding_incremental_start = coalesce_start_value("FUNDING", "2015-01-01")
defillama_incremental_start = coalesce_start_value("DEFILLAMA", "2021-10-01")
testing_enabled = ensure_bool("SQLMESH_TESTING_ENABLED", False)
