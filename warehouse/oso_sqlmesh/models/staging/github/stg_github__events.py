import typing as t
from datetime import datetime

import pandas as pd
from metrics_tools.models import constants
from sqlglot import exp
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model import ModelKindName


@model(
    name="oso.stg_github__events",
    # Actually this is a lie, we're going to return sql
    is_sql=False,
    dialect="trino",
    columns={
        "type": "VARCHAR",
        "public": "BOOLEAN",
        "payload": "VARCHAR",
        "repo": "ROW(id INT64, name VARCHAR, url VARCHAR)",
        "actor": "ROW(id INT64, login VARCHAR, gravatar_url VARCHAR, avatar_url VARCHAR, url VARCHAR)",
        "org": "ROW(id INT64, login VARCHAR, gravatar_url VARCHAR, avatar_url VARCHAR, url VARCHAR)",
        "created_at": "TIMESTAMP",
        "id": "VARCHAR",
        "other": "VARCHAR",
    },
    start=constants.github_incremental_start,
    kind={
        "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        "time_column": "created_at",
        "batch_size": 90,
        "batch_concurrency": 3,
        "lookback": 31,
        "forward_only": True,
    },
    partitioned_by=("day(created_at)",),
    physical_properties={"max_commit_retry": 15},
    audits=[
        ("has_at_least_n_rows", {"threshold": 0}),
        ("no_gaps", {"time_column": exp.to_column("created_at"), "no_gap_date_part": "day"}),
    ],
)
def github_events(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs,
) -> pd.DataFrame | exp.Expression:
    """We need to use a python model due to the way the github events are stored
    in bigquery. We need to generate a valid SQL based on the available tables
    in the github archive"""

    from functools import reduce

    import arrow

    runtime_stage = context.var('runtime_stage')

    if runtime_stage == "testing" or context.gateway != "trino":
        data = {
            "type": ["PushEvent"],
            "public": [True],
            "payload": [
                """
                {
                    "push_id": "123", 
                    "ref": "refs/head/main", 
                    "commits": [{"sha": "sha_value"}], 
                    "distinct_size": "1"
                }
            """
            ],
            "repo": [
                {
                    "id": 1,
                    "name": "name",
                    "url": "url",
                }
            ],
            "actor": [
                {
                    "id": 1,
                    "login": "login",
                    "gravatar_url": "gravatar_url",
                    "avatar_url": "avatar_url",
                    "url": "url",
                }
            ],
            "org": [
                {
                    "id": 1,
                    "login": "login",
                    "gravatar_url": "gravatar_url",
                    "avatar_url": "avatar_url",
                    "url": "url",
                }
            ],
            "created_at": [start],
            "id": ["a"],
            "other": [""],
        }
        df = pd.DataFrame(data)
        return df

    start_arrow = arrow.get(start)
    end_arrow = arrow.get(end)

    execution_time_arrow = arrow.get(execution_time)

    if end_arrow.floor("day") >= execution_time_arrow.floor("day"):
        # We can't select tables that are in the future so we will always be a
        # little behind
        end_arrow = execution_time_arrow.shift(days=-3)

    difference = end_arrow - start_arrow
    selects: t.List[exp.Select] = []
    if difference.days < 7:
        unit = "day"
        format = "YYYYMMDD"
    else:
        unit = "month"
        format = "YYYYMM"

    columns = [
        "type",
        "public",
        "payload",
        "repo",
        "actor",
        "org",
        "created_at",
        "id",
        "other",
    ]

    for period in arrow.Arrow.range(unit, start_arrow.floor(unit), end_arrow):
        selects.append(
            exp.select(*columns).from_(
                exp.to_table(f'"github_archive"."{unit}"."{period.format(format)}"')
            )
        )
    unioned_selects = reduce(lambda acc, cur: acc.union(cur, distinct=False), selects)
    return exp.select(*columns).from_(unioned_selects.subquery())
