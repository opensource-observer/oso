import logging
import random
import sys
import typing as t
from datetime import datetime, timedelta

import duckdb
import polars as pl
import pytest
from scheduler.testing.client import FakeUDMClient
from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def setup_debug_logging_for_tests() -> None:
    root_logger = logging.getLogger(__name__.split(".")[0])
    root_logger.setLevel(logging.DEBUG)
    sqlmesh_logger = logging.getLogger("sqlmesh")
    sqlmesh_logger.setLevel(logging.DEBUG)

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def generate_random_df(rows: int = 1000) -> pl.DataFrame:
    """Generates a random dataframe with specified number of rows."""
    # generate sample data
    n = 10
    now = datetime.now()

    df = pl.DataFrame(
        {
            "time": [now - timedelta(minutes=i * 5) for i in range(n)],
            "event_type": [
                random.choice(["login", "logout", "purchase", "view"]) for _ in range(n)
            ],
            "actor": [f"user_{random.randint(1, 5)}" for _ in range(n)],
            "value": [random.randint(1, 100) for _ in range(n)],
        }
    )
    return df


@pytest.fixture
def fake_udm_client() -> t.Iterator[FakeUDMClient]:
    """A fake user defined model client for testing purposes."""

    yield FakeUDMClient()


@pytest.fixture
def duckdb_engine_adapter() -> t.Iterator[DuckDBEngineAdapter]:
    """Creates a temporary sqlmesh project by copying the sample project"""

    conn = duckdb.connect(database=":memory:")

    # Add a dataframe to the in-memory database. With the following columns:
    # time: timestamp, event_type: str, actor: string, value: int
    # This table should be randomly generated with 1000 rows.
    df = generate_random_df(1000)  # noqa: F841

    # insert the dataframe into duckdb
    conn.execute("CREATE TABLE events AS SELECT * FROM df")

    adapter = DuckDBEngineAdapter(connection_factory_or_pool=lambda: conn)

    yield adapter
