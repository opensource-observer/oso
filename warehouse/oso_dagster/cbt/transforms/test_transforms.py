# ruff: noqa: F403

import arrow
import duckdb
import pytest
from oso_dagster.cbt.context import DataContext
from oso_dagster.cbt.duckdb import DuckDbConnector
from oso_dagster.cbt.transforms.time_constrain import (
    time_constrain,
    time_constrain_table,
)
from oso_dagster.utils.testing.duckdb import DuckDbFixture

SELECT_NO_CTE = """
SELECT *
FROM time_and_id
"""

SELECT_WITH_CTE = """
WITH cte AS (
    SELECT *
    FROM time_and_id
)
SELECT * FROM cte
"""

SELECT_WITH_JOIN = """
SELECT
  t1.*
FROM time_and_id t1
INNER JOIN time_id_and_name t2
  ON t1.id = t2.id
"""


@pytest.fixture
def db():
    fixture = DuckDbFixture.setup(
        {
            "time_and_id": [
                ["time", "id"],
                [arrow.get("2024-01-01", tzinfo="UTC").datetime, 1],
                [arrow.get("2024-02-01", tzinfo="UTC").datetime, 2],
                [arrow.get("2024-03-01", tzinfo="UTC").datetime, 3],
                [arrow.get("2024-04-01", tzinfo="UTC").datetime, 4],
            ],
            "time_id_and_name": [
                ["time", "id", "name"],
                [arrow.get("2024-01-01", tzinfo="UTC").datetime, 1, "alpha"],
                [arrow.get("2024-02-01", tzinfo="UTC").datetime, 2, "bravo"],
                [arrow.get("2024-03-01", tzinfo="UTC").datetime, 3, "charlie"],
                [arrow.get("2024-04-01", tzinfo="UTC").datetime, 4, "delta"],
                [arrow.get("2024-02-01", tzinfo="UTC").datetime, 5, "foxtrot"],
            ],
        }
    )
    yield fixture.db
    fixture.teardown()


@pytest.mark.parametrize(
    "query,time_constrain_args,expected_len",
    [
        (
            SELECT_NO_CTE,
            dict(
                start=arrow.get("2024-02-01", tzinfo="UTC"),
                end=arrow.get("2024-04-01", tzinfo="UTC"),
            ),
            2,
        ),
        (
            SELECT_WITH_CTE,
            dict(start=arrow.get("2024-02-01", tzinfo="UTC")),
            3,
        ),
    ],
)
def test_time_constrain_succeed(
    db: duckdb.DuckDBPyConnection,
    query: str,
    time_constrain_args: dict,
    expected_len: int,
):
    context = DataContext(DuckDbConnector(db))
    result = context.execute_query(
        query,
        [time_constrain("time", **time_constrain_args)],
    )
    assert len(result.fetchall()) == expected_len


@pytest.mark.parametrize(
    "query,table_name,time_constrain_args,expected_len",
    [
        (
            SELECT_WITH_JOIN,
            "time_id_and_name",
            dict(
                start=arrow.get("2024-02-01", tzinfo="UTC"),
                end=arrow.get("2024-04-01", tzinfo="UTC"),
            ),
            2,
        ),
    ],
)
def test_time_constrain_table_succeed(
    db: duckdb.DuckDBPyConnection,
    query: str,
    table_name: str,
    time_constrain_args: dict,
    expected_len: int,
):
    context = DataContext(DuckDbConnector(db))
    result = context.execute_query(
        query,
        [time_constrain_table("time", table_name, **time_constrain_args)],
    )
    assert len(result.fetchall()) == expected_len
