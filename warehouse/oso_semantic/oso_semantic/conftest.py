import os
import typing as t

import duckdb
import pandas as pd
import pytest

from .definition import Registry
from .testing import setup_registry

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(CURR_DIR, "fixtures")


@pytest.fixture
def semantic_registry() -> t.Iterator[Registry]:
    yield setup_registry()


@pytest.fixture
def semantic_db_conn() -> t.Iterator[duckdb.DuckDBPyConnection]:
    conn = duckdb.connect()

    csvs = [
        "artifacts_v1",
        "projects_v1",
        "collections_v1",
        "projects_by_collection_v1",
        "artifacts_by_project_v1",
        "artifacts_by_collection_v1",
        "int_events__github",
    ]

    conn.sql("CREATE SCHEMA oso;")

    for csv in csvs:
        path = os.path.join(FIXTURES_DIR, f"{csv}.csv")
        df = pd.read_csv(path)  # noqa: F841
        if csv == "int_events__github":
            print(df)
        table_name = f"oso.{csv}"
        conn.sql(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df;")

    yield conn
