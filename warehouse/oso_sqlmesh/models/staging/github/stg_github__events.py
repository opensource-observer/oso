import typing as t
from datetime import datetime

import orjson
import pandas as pd
from metrics_tools.models.constants import blockchain_incremental_start
from oso_dagster.assets.defillama import defillama_chain_mappings
from sqlglot import exp
from sqlmesh import ExecutionContext, model
from sqlmesh.core.model import ModelKindName


def parse_chain_tvl(protocol: str, chain_tvls_raw: str, start: datetime, end: datetime):
    """
    Extract aggregated TVL events from the chainTvls field.
    For each chain, each event is expected to have a date and a totalLiquidityUSD value.
    """
    series = []
    if isinstance(chain_tvls_raw, str):
        try:
            chain_tvls = orjson.loads(chain_tvls_raw)
            chains = chain_tvls.keys()
            # Flatten the dictionary to a table
            for chain in chains:
                tvl_history = chain_tvls[chain]["tvl"]
                if not tvl_history:
                    continue
                for entry in tvl_history:
                    # Skip entries outside the time range
                    if (
                        entry["date"] < start.timestamp()
                        or entry["date"] > end.timestamp()
                    ):
                        continue
                    amount = float(entry["totalLiquidityUSD"])
                    event = {
                        "time": pd.Timestamp(entry["date"], unit="s"),
                        "slug": protocol,
                        "protocol": protocol,
                        "chain": defillama_chain_mappings(chain),
                        "token": "",
                        "tvl": amount,
                        "event_type": "TVL",
                    }
                    series.append(event)
        except orjson.JSONDecodeError:
            return []
    return series


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
    runtime_stage: str,
    **kwargs,
):
    """We need to use a python model due to the way the github events are stored
    in bigquery. We need to generate a valid SQL based on the available tables
    in the github archive"""

    from functools import reduce

    import arrow

    if runtime_stage == "testing" or context.engine_adapter.dialect != "trino":
        data = {
            "type": ["PushEvent", "PullEvent", "IssueCommentEvent", "PullRequestEvent"],
            "public": [True, True, True, True],
            "payload": ["{}", "{}", "{}", "{}"],
            "repo": ["{}", "{}", "{}", "{}"],
            "actor": ["{}", "{}", "{}", "{}"],
            "org": ["{}", "{}", "{}", "{}"],
            "created_at": [start, start, start, start],
            "id": ["a", "b", "c", "d"],
            "other": ["", "", "", ""],
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
