from metrics_tools.semantic.definition import AttributeReference
from metrics_tools.semantic.query import QueryBuilder
from metrics_tools.semantic.testing import setup_registry
from sqlglot import exp


def test_query_builder():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.add_select(AttributeReference.from_string("event.time"))
    query.add_select(AttributeReference.from_string("event.event_source"))
    query.add_select(AttributeReference.from_string("event.from->artifact.name"))
    query.add_select(AttributeReference.from_string("event.to->collection.name"))

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