import typing as t

import pytest
from queryrewriter.resolvers.fake import FakeTableResolver
from queryrewriter.rewrite import rewrite_query
from queryrewriter.types import TableResolver
from sqlglot import exp, parse_one

# extend_sqlglot()


def compare_sql_queries(query1: str, query2: str) -> bool:
    """Compares two SQL queries for structural equality, ignoring formatting differences."""
    from sqlglot import parse_one
    from sqlglot.optimizer.qualify_tables import qualify_tables

    tree1 = qualify_tables(parse_one(query1), dialect="trino")
    tree2 = qualify_tables(parse_one(query2), dialect="trino")
    return tree1 == tree2


def assert_same_sql(query1: str, query2: str):
    sql_equal = compare_sql_queries(query1, query2)
    if not sql_equal:
        print("Expected Query:\n", parse_one(query2).sql(pretty=True))
        print("Actual Query:\n", parse_one(query1).sql(pretty=True))
    assert sql_equal, "SQL queries do not match structurally."


def reverse_table_name(table: exp.Table) -> str:
    parts = [table.catalog, table.db, table.name]
    return ".".join(reversed(list(filter(lambda x: x is not None and x != "", parts))))


@pytest.fixture
def fake_table_resolver():
    return FakeTableResolver(rewrite_rules=[reverse_table_name])


@pytest.mark.parametrize(
    "input_dialect,output_dialect,input_query,expected_query",
    [
        (
            "trino",
            "trino",
            """SELECT * FROM org1.dataset1.table1""",
            """SELECT * FROM table1.dataset1.org1 as table1""",
        ),
        (
            "trino",
            "trino",
            """SELECT * FROM table1""",
            """SELECT * FROM table1 as table1""",
        ),
        # Test with CTEs
        (
            "trino",
            "trino",
            """
            WITH cte AS (
                SELECT * FROM org1.dataset2.table2
            )
            SELECT * FROM cte
            JOIN org1.dataset1.table1 as "table1"
            ON cte.id = table1.id
            """,
            """
            WITH cte AS (
                SELECT * FROM table2.dataset2.org1 as table2
            )
            SELECT * FROM cte as cte
            JOIN table1.dataset1.org1 as table1
            ON cte.id = table1.id
            """,
        ),
        (
            "trino",
            "trino",
            """
            WITH cte AS (
                SELECT * FROM dataset2.table2
            )
            SELECT * FROM cte
            JOIN dataset1.table1 as "table1"
            ON cte.id = table1.id
            """,
            """
            WITH cte AS (
                SELECT * FROM table2.dataset2 as table2
            )
            SELECT * FROM cte as cte
            JOIN table1.dataset1 as table1
            ON cte.id = table1.id
            """,
        ),
        (
            # Test CTEs
            "trino",
            "trino",
            """
            SELECT * FROM dataset1.table1
            UNION ALL
            SELECT * FROM dataset2.table2
            UNION ALL
            SELECT * FROM dataset3.table3
            """,
            """
            SELECT * FROM table1.dataset1 as table1
            UNION ALL
            SELECT * FROM table2.dataset2 as table2
            UNION ALL
            SELECT * FROM table3.dataset3 as table3
            """,
        ),
        (
            # Test rewriting with macros
            "trino",
            "trino",
            """
            SELECT * FROM dataset1.table1
            WHERE created_at >= @start AND created_at < @end
            AND country = @some_macro_func('test')
            """,
            """
            SELECT * FROM table1.dataset1 as table1
            WHERE created_at >= @start AND created_at < @end
            AND country = @some_macro_func('test')
            """,
        ),
        (
            "trino",
            "trino",
            """SHOW CATALOGS""",
            """SHOW CATALOGS""",
        ),
        (
            "trino",
            "trino",
            """SHOW SCHEMAS FROM org1""",
            """SHOW SCHEMAS FROM org1""",
        ),
        (
            "trino",
            "trino",
            """SHOW TABLES FROM org1.dataset1""",
            """SHOW TABLES FROM org1.dataset1""",
        ),
        (
            # Noticed this regression where array indexing was being altered
            "trino",
            "trino",
            """SELECT ARRAY[1, 1.2, 4][2]""",
            """SELECT ARRAY[1, 1.2, 4][2]""",
        ),
        (
            "bigquery",
            "trino",
            """SELECT ARRAY[1, 1.2, 4][1]""",
            """SELECT ARRAY[1, 1.2, 4][2]""",
        ),
        (
            "trino",
            "trino",
            """
            WITH lifecycle_metrics AS (
            SELECT
                metric_id,
                metric_model
            FROM
                metrics_v0
            WHERE
                metric_event_source = 'GITHUB'
            )
            SELECT
            c.collection_name,
            c.display_name AS collection_display_name,
            ts.sample_date AS bucket_month,
            m.metric_model,
            ts.amount AS developers_count
            FROM
            timeseries_metrics_by_collection_v0 AS ts
            JOIN lifecycle_metrics AS lm USING (metric_id)
            JOIN metrics_v0 AS m USING (metric_id)
            JOIN collections_v1 AS c USING (collection_id)
            LIMIT 5
            """,
            """
            WITH lifecycle_metrics AS (
            SELECT
                metric_id,
                metric_model
            FROM metrics_v0 AS metrics_v0
            WHERE
                metric_event_source = 'GITHUB'
            )
            SELECT
            c.collection_name,
            c.display_name AS collection_display_name,
            ts.sample_date AS bucket_month,
            m.metric_model,
            ts.amount AS developers_count
            FROM timeseries_metrics_by_collection_v0 AS ts
            JOIN lifecycle_metrics AS lm
            USING (metric_id)
            JOIN metrics_v0 AS m
            USING (metric_id)
            JOIN collections_v1 AS c
            USING (collection_id)
            LIMIT 5
            """,
        ),
    ],
)
@pytest.mark.asyncio
async def test_rewrite_query(
    fake_table_resolver: TableResolver,
    input_dialect: str,
    output_dialect: str,
    input_query: str,
    expected_query: str,
):
    resolvers: t.List[TableResolver] = [fake_table_resolver]

    response = await rewrite_query(
        query=input_query,
        table_resolvers=resolvers,
        input_dialect=input_dialect,
        output_dialect=output_dialect,
    )
    assert_same_sql(response.rewritten_query, expected_query)


@pytest.mark.parametrize(
    "input_dialect,output_dialect,input_query,error_string,rewrite_rules",
    [
        (
            "trino",
            "trino",
            """
            WITH "test" (
                select * from "test" where id = 1
            ), "boop" (
                select * from "test"
            )
            select * from "test"
            """,
            "circular reference",
            None,
        ),
        (
            "trino",
            "trino",
            """SELECT * FROM non_existent_table""",
            "Tables do not exist",
            [],
        ),
    ],
)
@pytest.mark.asyncio
async def test_inputs_should_fail(
    fake_table_resolver: FakeTableResolver,
    input_dialect: str,
    output_dialect: str,
    input_query: str,
    error_string: str,
    rewrite_rules: list[t.Callable[[exp.Table], str | None]] | None,
):
    if rewrite_rules is not None:
        fake_table_resolver.set_rewrite_rules(rewrite_rules)
    resolvers: t.List[TableResolver] = [fake_table_resolver]
    try:
        await rewrite_query(
            query=input_query,
            table_resolvers=resolvers,
            input_dialect=input_dialect,
            output_dialect=output_dialect,
        )
    except Exception as e:
        assert error_string in str(e), f"Expected an error message with: {error_string}"
    else:
        assert False, "Expected an exception but none was raised."
