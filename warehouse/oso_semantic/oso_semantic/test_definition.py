import duckdb
import pandas as pd
from sqlglot import parse_one

from .definition import (
    AttributePath,
    AttributePathTransformer,
    BoundMeasure,
    Dimension,
    Measure,
    Model,
    Registry,
    SemanticQuery,
)
from .testing import setup_registry


def test_attribute_reference_traversal():

    ref1 = AttributePath.from_string("a.b->c.d->e.f")
    ref2 = AttributePath(path=["a.b", "c.d", "e.f"])
    ref3 = AttributePath(path=["a.b", "c.d", "x.y"])
    ref4 = AttributePath(path=["a.g", "c.d", "e.f"])
    assert ref1 == ref2
    assert ref1 != ref3

    t1 = ref1.traverser()
    t2 = ref2.traverser()

    assert t1.current_model_name == t2.current_model_name
    assert t1.current_table_alias == t2.current_table_alias

    while t1.next() and t2.next():
        assert t1.current_model_name == t2.current_model_name
        assert t1.current_table_alias == t2.current_table_alias
        assert t1.current_attribute_name == t2.current_attribute_name
        assert t1.alias("foo") == t2.alias("foo")

    while t1.prev():
        pass

    t3 = ref3.traverser()

    t1.next()
    t3.next()

    assert t1.current_table_alias == t3.current_table_alias
    print(t1.alias_stack)
    print(t3.alias_stack)
    assert t1.alias("foo") == t3.alias("foo")

    t1.next()
    t3.next()

    assert t1.current_attribute_name != t3.current_attribute_name
    assert t1.alias("foo") == t3.alias("foo")

    while t1.prev():
        pass

    t4 = ref4.traverser()

    assert t1.alias("foo") == t4.alias("foo")

    t1.next()
    t4.next()

    assert t1.alias("foo") != t4.alias("foo")


def test_semantic_model_shortest_path():
    registry = setup_registry()

    assert registry.dag.join_paths("github_event", "artifact") == (
        ["github_event", "artifact"],
        ["artifact"],
    )

    assert registry.dag.join_paths("artifact", "github_event") == (
        ["artifact"],
        ["github_event", "artifact"],
    )

    assert registry.dag.join_paths("artifact", "project") == (
        ["artifact", "project"],
        ["project"],
    )

    assert registry.dag.join_paths("github_event", "collection") == (
        ["github_event", "artifact", "project", "collection"],
        ["collection"],
    )

    to_artifact_ref = registry.get_model("github_event").find_relationship(
        model_ref="artifact", name="to"
    )
    from_artifact_ref = registry.get_model("github_event").find_relationship(
        model_ref="artifact", name="from"
    )

    assert to_artifact_ref.model_ref == "artifact"
    assert to_artifact_ref.name == "to"
    assert to_artifact_ref.foreign_key_column == "to_artifact_id"
    assert from_artifact_ref.model_ref == "artifact"
    assert from_artifact_ref.name == "from"
    assert from_artifact_ref.foreign_key_column == "from_artifact_id"


def test_semantic_query(semantic_db_conn: duckdb.DuckDBPyConnection):
    registry = setup_registry()

    query = SemanticQuery(
        selects=[
            "github_event.event_type AS event_type",
            "github_event.to->collection.name AS collection_name",
            "github_event.total_amount AS total_amount",
        ],
        filters=[
            "github_event.from->artifact.name = 'repo1'",
        ],
    )

    query_exp = registry.query(query)
    assert query_exp is not None
    print(query_exp.sql(dialect="duckdb", pretty=True))

    result = semantic_db_conn.sql(query_exp.sql(dialect="duckdb"))
    result_df = result.df()
    result_df = result_df.sort_values(by=["collection_name"])
    result_df = result_df.reset_index(drop=True)
    print(result_df)

    pd.testing.assert_frame_equal(
        result_df,
        pd.DataFrame(
            {
                "event_type": ["COMMIT_CODE", "COMMIT_CODE", "COMMIT_CODE"],
                "collection_name": ["collection1", "collection2", "collection3"],
                "total_amount": [7.0, 7.0, 7.0],
            }
        ),
        check_like=True,
    )


def test_resolve_attributes_to_query_part(semantic_registry: Registry):
    # Test resolving a single attribute
    ref0 = AttributePath.from_string("artifact.name")

    resolved_query_part0 = ref0.resolve(semantic_registry)
    assert resolved_query_part0 is not None
    assert (
        resolved_query_part0.expression.sql(dialect="duckdb")
        == "$SEMANTIC_REF('artifact.artifact_name')"
    )

    parent_path = AttributePath.from_string("github_event.to->artifact.id")
    parent_traverser = parent_path.traverser()
    while parent_traverser.next():
        pass
    scoped_resolved_query_part = ref0.resolve(
        semantic_registry, parent_traverser=parent_traverser
    )

    assert scoped_resolved_query_part is not None
    assert (
        scoped_resolved_query_part.expression.sql(dialect="duckdb")
        == "$SEMANTIC_REF('github_event.to->artifact.artifact_name')"
    )

    ref1 = AttributePath.from_string("github_event.from->artifact.name")
    resolved_query_part1 = ref1.resolve(semantic_registry)
    assert resolved_query_part1 is not None
    assert (
        resolved_query_part1.expression.sql(dialect="duckdb")
        == "$SEMANTIC_REF('github_event.from->artifact.artifact_name')"
    )


def test_attribute_reference_transformer():
    simple_column = parse_one("github_event.to")
    transformer0 = AttributePathTransformer()
    transformed_result0 = transformer0.transform(simple_column)
    assert transformed_result0 is not None
    assert len(transformed_result0.references) == 1
    assert transformed_result0.references[0] == AttributePath.from_string(
        "github_event.to"
    )

    multiple_refs_sql = parse_one(
        "github_event.to->artifact.count > github_event.from->artifact.count"
    )

    transformer1 = AttributePathTransformer()
    transformed_result1 = transformer1.transform(multiple_refs_sql)

    assert transformed_result1 is not None
    assert transformed_result1.node != multiple_refs_sql
    assert len(transformed_result1.references) == 2

    assert (
        AttributePath.from_string("github_event.to->artifact.count")
        in transformed_result1.references
    )
    assert (
        AttributePath.from_string("github_event.from->artifact.count")
        in transformed_result1.references
    )


def test_resolve_metrics():
    # registry = setup_registry()

    registry = Registry()

    model = Model(
        name="artifact",
        table="oso.artifacts_v1",
        description="An artifact",
        dimensions=[
            Dimension(name="id", column_name="artifact_id"),
        ],
        primary_key="artifact_id",
        measures=[
            Measure(
                name="count",
                description="The number of artifacts",
                query="COUNT(self.id)",
            )
        ],
    )
    registry.register(model)

    metric = model.get_attribute("count")

    assert isinstance(metric, BoundMeasure), "count should be a BoundMetric"
    assert metric is not None, "metric should not be None"

    ref = AttributePath.from_string("artifact.id")
    traverser = ref.traverser()

    query_part = metric.to_query_part(traverser, ref, registry)

    assert query_part.resolved_references == [ref]
