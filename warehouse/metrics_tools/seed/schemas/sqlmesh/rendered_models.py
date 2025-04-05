from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class RenderedModels(BaseModel):
    model_name: str | None = Column("VARCHAR")
    rendered_sql: str | None = Column("VARCHAR")
    rendered_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    dlt_load_id: str = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="sqlmesh",
    table="rendered_models",
    base=RenderedModels,
    rows=[
        RenderedModels(
            model_name="stg_github__distinct_main_commits",
            rendered_sql='WITH "deduped_commits" AS (SELECT * FROM github_commits WHERE 1=1)',
            rendered_at=datetime(2025, 3, 27, 22, 3, 29, 163110),
            dlt_load_id="1743109399.194649",
            dlt_id="aSe/ejttoOfiGA",
        ),
        RenderedModels(
            model_name="int_all_artifacts",
            rendered_sql='WITH "onchain_artifacts" AS (SELECT * FROM deployers WHERE 1=1)',
            rendered_at=datetime(2025, 3, 27, 22, 3, 34, 629756),
            dlt_load_id="1743109399.194649",
            dlt_id="OU72RpbQ0bJgAQ",
        ),
        RenderedModels(
            model_name="int_contracts_transactions_weekly",
            rendered_sql='SELECT DATE_TRUNC(\'WEEK\', "traces"."dt") AS "week" FROM traces WHERE 1=1',
            rendered_at=datetime(2025, 3, 27, 22, 3, 33, 118413),
            dlt_load_id="1743109399.194649",
            dlt_id="z66vGMH5WnmO/g",
        ),
        RenderedModels(
            model_name="int_derived_contracts_sort_weights",
            rendered_sql='SELECT UPPER("derived_contracts"."chain") FROM derived_contracts WHERE 1=1',
            rendered_at=datetime(2025, 3, 27, 22, 3, 32, 967688),
            dlt_load_id="1743109399.194649",
            dlt_id="GY6hZ5Ir6NhESw",
        ),
        RenderedModels(
            model_name="int_superchain_s7_onchain_metrics_by_project",
            rendered_sql='WITH "base_events" AS (SELECT * FROM events WHERE 1=1)',
            rendered_at=datetime(2025, 3, 27, 22, 3, 38, 551416),
            dlt_load_id="1743109399.194649",
            dlt_id="WjrTD49+rmJhkA",
        ),
    ],
)
