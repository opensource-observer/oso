import pytest
import sqlglot
from scheduler.evaluator import evaluate_all_models
from scheduler.testing.client import FakeUDMClient
from scheduler.types import Model
from sqlglot import exp
from sqlmesh.core.engine_adapter.duckdb import DuckDBEngineAdapter


def to_datatype(type_str: str) -> exp.DataType:
    return sqlglot.parse_one(type_str, into=exp.DataType)


# def test_materialize(duckdb_engine_adapter: DuckDBEngineAdapter) -> None:
#     expr = t.cast(exp.Select, sqlglot.parse_one("SELECT actor, SUM(value) as total FROM events GROUP BY actor"))

#     target_columns_to_types = {
#         "actor": to_datatype("VARCHAR"),
#         "total": to_datatype("INTEGER"),
#     }

#     duckdb_engine_adapter.create_table(
#         table_name="aggregated_events",
#         target_columns_to_types=target_columns_to_types,
#         exists=True
#     )

#     duckdb_engine_adapter.insert_append(
#         table_name="aggregated_events",
#         query_or_df=expr,
#         target_columns_to_types=target_columns_to_types,
#     )

#     df = duckdb_engine_adapter.fetchdf("SELECT * FROM aggregated_events")
#     # Count the number of rows in the dataframe
#     distinct_actor_df = duckdb_engine_adapter.fetchdf("SELECT COUNT(DISTINCT actor) FROM events")
#     # Get the count value
#     distinct_actor_count = distinct_actor_df.iloc[0, 0]

#     assert len(df) == distinct_actor_count


@pytest.mark.asyncio
async def test_evaluator(
    duckdb_engine_adapter: DuckDBEngineAdapter, fake_udm_client: FakeUDMClient
) -> None:
    fake_udm_client.add_model(
        Model(
            org_id="00000000-0000-0000-0000-000000000001",
            org_name="Test Org",
            id="00000000-0000-0000-0000-000000000001",
            name="aggregated_events",
            dataset_id="00000000-0000-0000-0000-000000000001",  # fake uuid
            dataset_name="aggregated_events",
            language="sql",
            code="""
                SELECT actor, SUM(value) as total
                FROM events
                GROUP BY actor
            """,
        )
    )

    await evaluate_all_models(
        udm_client=fake_udm_client,
        adapter=duckdb_engine_adapter,
    )

    schemas = duckdb_engine_adapter.fetchdf("SHOW ALL TABLES")
    # Print all rows and all columns in the schemas dataframe for debugging
    print(schemas.to_string())

    df = duckdb_engine_adapter.fetchdf(
        """SELECT * FROM "ds_00000000000000000000000000000001"."tbl_00000000000000000000000000000001" """
    )
    # Count the number of rows in the dataframe
    distinct_actor_df = duckdb_engine_adapter.fetchdf(
        "SELECT COUNT(DISTINCT actor) FROM events"
    )
    # Get the count value
    distinct_actor_count = distinct_actor_df.iloc[0, 0]

    assert len(df) == distinct_actor_count
