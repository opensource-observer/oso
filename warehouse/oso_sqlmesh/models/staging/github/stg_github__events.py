import typing as t
from datetime import datetime

import pandas as pd
from metrics_tools.models.constants import blockchain_incremental_start
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
    start=blockchain_incremental_start,
    kind={
        "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
        "time_column": "created_at",
        "batch_size": 90,
        "lookback": 7,
    },
    partitioned_by=("day(created_at)",),
)
def github_events(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    gateway: str,
    runtime_stage: str,
    **kwargs,
):
    """We need to use a python model due to the way the github events are stored
    in bigquery. We need to generate a valid SQL based on the available tables
    in the github archive"""

    from functools import reduce

    import arrow

    if runtime_stage == "testing" or gateway != "trino":
        data = {
            "type": ["PushEvent"],
            "public": [True],
            "payload": ["{}"],
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
        yield df
        return

    start_arrow = arrow.get(start)
    end_arrow = arrow.get(end)

    difference = start_arrow - end_arrow
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
    for period in arrow.Arrow.range(unit, start_arrow.floor(unit), end):
        selects.append(
            exp.select(*columns).from_(f"github_archive.{unit}.{period.format(format)}")
        )
    unioned_selects = reduce(lambda acc, cur: acc.union(cur), selects)

    return exp.select(*columns).from_(unioned_selects)
