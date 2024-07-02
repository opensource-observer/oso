from dlt.sources import incremental
from ..factories.sql import sql_assets
from ..utils.secrets import SecretReference

ecosystems = sql_assets(
    "ecosystems",
    SecretReference(group_name="ecosystems", key="main_database"),
    [{"table": "fake_timeseries", "incremental": incremental("time")}],
)
