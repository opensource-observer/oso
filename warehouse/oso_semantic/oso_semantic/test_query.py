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

    joins = list(query_exp.find_all(exp.From)) + list(query_exp.find_all(exp.Join))

    assert len(joins) == 3

    tables = [j.this for j in joins]
    tables_count = {}
    for table in tables:
        table_count = tables_count.get(table.name, 0)
        tables_count[table.name] = table_count + 1

    assert tables_count["projects_v1"] == 1
    assert tables_count["collections_v1"] == 1


def test_query_builder_with_metric_and_filtered_dimension():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.select("projects.count")
    query.where("projects.by_collection->collections.collection_name = 'optimism'")

    query_exp = query.build()

    assert query_exp.expressions is not None
    assert len(query_exp.expressions) == 1
    alias = query_exp.expressions[0].alias
    assert alias == "projects_count"
    count_exp = query_exp.expressions[0].this
    assert isinstance(count_exp, exp.Count)
    column_exp = count_exp.this
    assert isinstance(column_exp, exp.Column)
    column_name_identifier = column_exp.this
    assert isinstance(column_name_identifier, exp.Identifier)
    assert column_name_identifier.this == "project_id"