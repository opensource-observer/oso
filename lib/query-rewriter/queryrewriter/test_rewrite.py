import typing as t

import pytest
from queryrewriter.rewrite import rewrite_query
from queryrewriter.types import TableResolver
from sqlglot import exp, parse_one

# extend_sqlglot()


def compare_sql_queries(query1: str, query2: str) -> bool:
    """Compares two SQL queries for structural equality, ignoring formatting differences."""
    from sqlglot import parse_one
    from sqlglot.optimizer.qualify import qualify

    tree1 = qualify(parse_one(query1))
    tree2 = qualify(parse_one(query2))
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
    from queryrewriter.resolvers.fake import FakeTableResolver

    return FakeTableResolver(rewrite_rules=[reverse_table_name])


@pytest.mark.parametrize(
    "input_query,expected_query",
    [
        (
            """SELECT * FROM org1.dataset1.table1""",
            '''SELECT * FROM "table1"."dataset1"."org1" as "table1"''',
        ),
        (
            """SELECT * FROM table1""",
            '''SELECT * FROM "table1" as "table1"''',
        ),
        # Test with CTEs
        (
            """
            WITH cte AS (
                SELECT * FROM org1.dataset2.table2
            ) 
            SELECT * FROM cte 
            JOIN org1.dataset1.table1 as "table1"
            ON cte.id = table1.id
            """,
            """
            WITH "cte" AS (
                SELECT * FROM "table2"."dataset2"."org1" as "table2"
            ) 
            SELECT * FROM "cte" as "cte"
            JOIN "table1"."dataset1"."org1" as "table1"
            ON "cte"."id" = "table1"."id"
            """,
        ),
        (
            """
            WITH cte AS (
                SELECT * FROM dataset2.table2
            ) 
            SELECT * FROM cte 
            JOIN dataset1.table1 as "table1"
            ON cte.id = table1.id
            """,
            """
            WITH "cte" AS (
                SELECT * FROM "table2"."dataset2" as "table2"
            ) 
            SELECT * FROM "cte" as "cte"
            JOIN "table1"."dataset1" as "table1"
            ON "cte"."id" = "table1"."id"
            """,
        ),
        (
            # Test CTEs
            """
            SELECT * FROM dataset1.table1
            UNION ALL
            SELECT * FROM dataset2.table2
            UNION ALL
            SELECT * FROM dataset3.table3
            """,
            """
            SELECT * FROM "table1"."dataset1" as "table1"
            UNION ALL
            SELECT * FROM "table2"."dataset2" as "table2"
            UNION ALL
            SELECT * FROM "table3"."dataset3" as "table3"
            """,
        ),
        (
            # Test rewriting with macros
            """
            SELECT * FROM dataset1.table1
            WHERE created_at >= @start AND created_at < @end
            AND country = @some_macro_func('test')
            """,
            """
            SELECT * FROM "table1"."dataset1" as "table1"
            WHERE "created_at" >= @start AND "created_at" < @end
            AND "country" = @some_macro_func('test')
            """,
        ),
        (
            """SHOW CATALOGS""",
            """SHOW CATALOGS""",
        ),
        (
            """SHOW SCHEMAS FROM org1""",
            """SHOW SCHEMAS FROM org1""",
        ),
        (
            """SHOW TABLES FROM org1.dataset1""",
            """SHOW TABLES FROM org1.dataset1""",
        ),
    ],
)
@pytest.mark.asyncio
async def test_rewrite_query(
    fake_table_resolver: TableResolver,
    input_query: str,
    expected_query: str,
):
    resolvers: t.List[TableResolver] = [fake_table_resolver]

    response = await rewrite_query(
        query=input_query,
        table_resolvers=resolvers,
        dialect="trino",
    )
    assert_same_sql(response.rewritten_query, expected_query)


@pytest.mark.parametrize(
    "input_query,error_string",
    [
        (
            """
            WITH "test" (
                select * from "test" where id = 1
            ), "boop" (
                select * from "test"
            )
            select * from "test"
            """,
            "circular reference",
        )
    ],
)
@pytest.mark.asyncio
async def test_inputs_should_fail(
    fake_table_resolver: TableResolver,
    input_query: str,
    error_string: str,
):
    resolvers: t.List[TableResolver] = [fake_table_resolver]
    try:
        await rewrite_query(
            query=input_query,
            table_resolvers=resolvers,
            dialect="trino",
        )
    except Exception as e:
        assert error_string in str(e), f"Expected an error message with: {error_string}"
    else:
        assert False, "Expected an exception but none was raised."
