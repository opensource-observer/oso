from sqlglot import exp

from .query import QueryBuilder
from .testing import setup_registry


def test_query_builder_with_dimensions():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.select("int_events__github.month AS event_month")
    query.select("int_events__github.event_source AS event_source")
    query.select("int_events__github.from->artifacts.artifact_name")
    query.select("int_events__github.to->collections.collection_name")
    query.where("int_events__github.month = DATE '2023-01-01'")

    query_exp = query.build()

    print(query_exp.sql(pretty=True, dialect="duckdb"))

    joins = list(query_exp.find_all(exp.Join))

    assert len(joins) == 4

    tables = [j.this for j in joins]
    tables_count = {}
    for table in tables:
        table_count = tables_count.get(table.name, 0)
        tables_count[table.name] = table_count + 1

    assert tables_count["artifacts_v1"] == 2
    assert tables_count["collections_v1"] == 1


def test_query_builder_with_metrics():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.select("collections.collection_name")
    query.select("projects.count AS project_count")

    query_exp = query.build()

    print(query_exp.sql(pretty=True, dialect="duckdb"))

    joins = list(query_exp.find_all(exp.From)) + list(query_exp.find_all(exp.Join))

    assert len(joins) == 3

    tables = [j.this for j in joins]
    tables_count = {}
    for table in tables:
        table_count = tables_count.get(table.name, 0)
        tables_count[table.name] = table_count + 1

    assert tables_count["projects_v1"] == 1
    assert tables_count["collections_v1"] == 1
