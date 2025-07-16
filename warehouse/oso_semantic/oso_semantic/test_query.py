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


def test_query_builder_to_model():
    registry = setup_registry()

    query = QueryBuilder(registry)
    query.select("int_events__github.month AS event_month")
    query.select("int_events__github.event_type AS event_type")
    query.select("int_events__github.event_source")
    query.select("int_events__github.from->artifacts.artifact_name")
    query.select("int_events__github.count")
    query.select("int_events__github.from AS artifact_id")

    # Attempt to convert the query to a model
    model = query.to_model("test_model")

    model.dimensions.sort(key=lambda d: d.name)

    assert model.name == "test_model"
    assert model.table == "test_model"
    assert len(model.dimensions) == 5
    assert model.dimensions[0].name == "event_month"
    assert model.dimensions[1].name == "event_type"
    assert model.dimensions[2].name == "int_events__github_count"
    assert model.dimensions[3].name == "int_events__github_event_source"
    assert (
        model.dimensions[4].name == "int_events__github_from__artifacts_artifact_name"
    )
    assert len(model.relationships) == 1
    assert model.relationships[0].name == "artifact_id"


def test_query_builder_with_cte():
    registry = setup_registry()

    # Create the first query and convert it to a CTE
    base_query = QueryBuilder(registry)
    base_query.select("int_events__github.month AS event_month")
    base_query.select("int_events__github.event_source AS event_source")
    base_query.select("int_events__github.to")

    # Register the CTE
    cte_name = "github_push_events"

    # Create a new query that references the CTE
    new_query = QueryBuilder(registry)
    new_query.cte(cte_name, base_query)
    new_query.select(f"{cte_name}.event_month")
    new_query.select(f"{cte_name}.event_source")
    new_query.where(f"{cte_name}.event_month = DATE '2023-01-01'")

    # Build the final query
    query_exp = new_query.build()

    # Assertions to validate the query structure
    assert query_exp is not None
    assert len(list(query_exp.find_all(exp.From))) == 2  # Ensure the CTE is referenced
    assert (
        len(list(query_exp.find_all(exp.Join))) == 0
    )  # No joins expected in this case
