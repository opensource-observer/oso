from sqlglot import exp

from .definition import AttributePath, Filter
from .query import QueryBuilder
from .testing import setup_registry


def test_query_builder_with_dimensions():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.add_select(AttributePath.from_string("github_event.month"), "event_month")
    query.add_select(
        AttributePath.from_string("github_event.event_source"), "event_source"
    )
    query.add_select(
        AttributePath.from_string("github_event.from->artifact.name"), "artifact_name"
    )
    query.add_select(
        AttributePath.from_string("github_event.to->collection.name"), "collection_name"
    )
    query.add_filter(Filter(query="github_event.month = DATE '2023-01-01'"))

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
    query.add_select(AttributePath.from_string("collection.name"), "collection_name")
    query.add_select(AttributePath.from_string("project.count"), "project_count")

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
