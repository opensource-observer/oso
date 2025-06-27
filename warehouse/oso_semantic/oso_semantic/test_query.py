from sqlglot import exp

from .query import QueryBuilder
from .testing import setup_registry


def test_query_builder_with_dimensions():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.select("github_event.month AS event_month")
    query.select("github_event.event_source AS event_source")
    query.select("github_event.from->artifact.name AS artifact_name")
    query.select("github_event.to->collection.name AS collection_name")
    query.where("github_event.month = DATE '2023-01-01'")

    query_exp = query.build()

    print(query_exp.sql(pretty=True, dialect="duckdb"))

    joins = list(query_exp.find_all(exp.Join))

    assert len(joins) == 6

    tables = [j.this for j in joins]
    tables_count = {}
    for table in tables:
        table_count = tables_count.get(table.name, 0)
        tables_count[table.name] = table_count + 1

    assert tables_count["artifacts_v1"] == 2
    assert tables_count["projects_v1"] == 1
    assert tables_count["collections_v1"] == 1


def test_query_builder_with_metrics():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.select("collection.name AS collection_name")
    query.select("project.count AS project_count")

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
