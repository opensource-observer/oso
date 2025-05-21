from metrics_tools.semantic.definition import AttributeReference
from metrics_tools.semantic.example import setup_registry
from metrics_tools.semantic.query import QueryBuilder


def test_query_builder():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.add_select(AttributeReference.from_string("event.time"))
    query.add_select(AttributeReference.from_string("event.event_source"))
    query.add_select(AttributeReference.from_string("event.from->artifact.name"))
    query.add_select(AttributeReference.from_string("event.to->collection.name"))

    print(query.build().sql(dialect="duckdb", pretty=True))