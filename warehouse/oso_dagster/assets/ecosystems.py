from dlt.sources import incremental
from oso_dagster.factories import sql_assets
from oso_dagster.utils import SecretReference

# ecosystems_papers = sql_assets(
#     "ecosystems",
#     SecretReference(group_name="ecosystems", key="papers_database"),
#     [
#         {
#             "table": "papers",
#             "incremental": incremental("updated_at"),
#             "destination_table_name": "papers",
#         },
#         {
#             "table": "projects",
#             "incremental": incremental("updated_at"),
#             "destination_table_name": "papers_projects",
#         },
#     ],
# )

ecosystems_advisories = sql_assets(
    "ecosystems",
    SecretReference(group_name="ecosystems", key="advisories_databae"),
    [
        {
            "table": "advisories",
            "incremental": incremental("updated_at"),
        }
    ],
    group_name="advisories",
)
