
from ..factories.sql import sql_assets
from ..utils.secrets import SecretReference

regendata_xyz = sql_assets(
    "gitcoin",
    SecretReference(
        group_name="gitcoin",
        key="regendata_xyz_database",
    ),
    [
        {
            "table": "all_donations",
            "write_disposition": "replace",
        },
        {
            "table": "project_groups_summary",
            "write_disposition": "replace",
        },
        {
            "table": "project_lookup",
            "write_disposition": "replace",
        },
        {
            "table": "all_matching",
            "write_disposition": "replace",
        },
    ],
)
