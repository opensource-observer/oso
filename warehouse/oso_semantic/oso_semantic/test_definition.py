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
    ModelHasNoJoinPath,
    Registry,
    Relationship,
    RelationshipType,
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

    artifact_project_tree = registry.dag.find_best_join_tree(
        [
            AttributePath(
                path=["artifact.id", "artifacts_by_project.project_id", "project.id"]
            ),
        ]
    )
    github_artifact_tree = registry.dag.find_best_join_tree(
        [
            AttributePath.from_string("github_event.to->artifact.id"),
        ]
    )
    github_collection_tree = registry.dag.find_best_join_tree(
        [
            AttributePath.from_string("github_event.to->collection.id"),
        ]
    )

    assert github_artifact_tree.get_path("github_event", "artifact") == [
        "github_event",
        "artifact",
    ]

    assert github_artifact_tree.get_path("artifact", "github_event") == [
        "artifact",
        "github_event",
    ]

    assert artifact_project_tree.get_path("artifact", "project") == [
        "artifact",
        "artifacts_by_project",
        "project",
    ]

    assert github_collection_tree.get_path("github_event", "collection") == [
        "github_event",
        "artifact",
        "artifacts_by_project",
        "project",
        "projects_by_collection",
        "collection",
    ]

    to_artifact_ref = registry.get_model("github_event").find_relationship(
        model_ref="artifact", name="to"
    )
    from_artifact_ref = registry.get_model("github_event").find_relationship(
        model_ref="artifact", name="from"
    )

    assert to_artifact_ref.ref_model == "artifact"
    assert to_artifact_ref.name == "to"
    assert to_artifact_ref.source_foreign_key[0] == "to_artifact_id"
    assert from_artifact_ref.ref_model == "artifact"
    assert from_artifact_ref.name == "from"
    assert from_artifact_ref.source_foreign_key[0] == "from_artifact_id"


def test_semantic_query(semantic_db_conn: duckdb.DuckDBPyConnection):
    registry = setup_registry()

    query = registry.select(
        "github_event.event_type AS event_type",
        "github_event.to->collection.name AS collection_name",
        "github_event.total_amount AS total_amount",
    ).where("github_event.from->artifact.name = 'repo1'")

    query_exp = query.build()
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


def test_registry_cycle_detection():
    """Test that the registry can detect cycles in model relationships."""
    from .definition import Model, Registry, Relationship, RelationshipType

    registry = Registry()

    # Create models that form a cycle: A -> B -> C -> A
    model_a = Model(
        name="model_a",
        table="table_a",
        relationships=[
            Relationship(
                name="to_b",
                ref_model="model_b",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="b_id",
                ref_key="id",
            )
        ],
        dimensions=[],
        measures=[],
    )

    model_b = Model(
        name="model_b",
        table="table_b",
        relationships=[
            Relationship(
                name="to_c",
                ref_model="model_c",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="c_id",
                ref_key="id",
            )
        ],
        dimensions=[],
        measures=[],
    )

    model_c = Model(
        name="model_c",
        table="table_c",
        relationships=[
            Relationship(
                name="to_a",
                ref_model="model_a",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="a_id",
                ref_key="id",
            )
        ],
        dimensions=[],
        measures=[],
    )

    # Register models (this creates the cycle)
    registry.register(model_a)
    registry.register(model_b)
    registry.register(model_c)

    # Test that querying raises an error when cycle is detected
    try:
        registry.select("model_a.id")
        assert False, "Should have raised ValueError due to cycle"
    except ValueError as e:
        assert "Cycle detected" in str(e), f"Expected cycle error, got: {e}"


def test_registry_no_cycle():
    """Test that the registry correctly identifies when there are no cycles."""
    from .definition import Model, Registry, Relationship, RelationshipType

    registry = Registry()

    # Create models without cycles: A -> B -> C (no back edges)
    model_a = Model(
        name="model_a",
        table="table_a",
        relationships=[
            Relationship(
                name="to_b",
                ref_model="model_b",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="b_id",
                ref_key="id",
            )
        ],
        dimensions=[],
        measures=[],
    )

    model_b = Model(
        name="model_b",
        table="table_b",
        relationships=[
            Relationship(
                name="to_c",
                ref_model="model_c",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="c_id",
                ref_key="id",
            )
        ],
        dimensions=[],
        measures=[],
    )

    model_c = Model(
        name="model_c",
        table="table_c",
        relationships=[],  # No relationships - end of chain
        dimensions=[],
        measures=[],
    )

    # Register models
    registry.register(model_a)
    registry.register(model_b)
    registry.register(model_c)

    # Test that no cycle is detected
    registry.dag.check_cycle()


def test_dag_find_best_join_tree():
    """Test that find_best_join_tree returns the smallest possible tree."""
    from .definition import (
        AttributePath,
        Dimension,
        Model,
        Registry,
        Relationship,
        RelationshipType,
    )

    registry = Registry()

    # Create a simpler model graph for clearer testing:
    # A -> B -> D
    # A -> C -> D
    # This gives us two possible paths from A to D

    model_a = Model(
        name="model_a",
        table="table_a",
        relationships=[
            Relationship(
                name="to_b",
                ref_model="model_b",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="b_id",
                ref_key="id",
            ),
            Relationship(
                name="to_c",
                ref_model="model_c",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="c_id",
                ref_key="id",
            ),
        ],
        dimensions=[
            Dimension(name="id", description="A's ID"),
            Dimension(name="name", description="A's name"),
        ],
        measures=[],
    )

    model_b = Model(
        name="model_b",
        table="table_b",
        relationships=[
            Relationship(
                name="to_d",
                ref_model="model_d",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="d_id",
                ref_key="id",
            )
        ],
        dimensions=[
            Dimension(name="id", description="B's ID"),
            Dimension(name="name", description="B's name"),
        ],
        measures=[],
    )

    model_c = Model(
        name="model_c",
        table="table_c",
        relationships=[
            Relationship(
                name="to_d",
                ref_model="model_d",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="d_id",
                ref_key="id",
            )
        ],
        dimensions=[
            Dimension(name="id", description="C's ID"),
            Dimension(name="name", description="C's name"),
        ],
        measures=[],
    )

    model_d = Model(
        name="model_d",
        table="table_d",
        relationships=[],
        dimensions=[
            Dimension(name="id", description="D's ID"),
            Dimension(name="value", description="D's value"),
        ],
        measures=[],
    )

    # Register all models
    registry.register(model_a)
    registry.register(model_b)
    registry.register(model_c)
    registry.register(model_d)

    # Test 1: Simple case - only need A
    references_a_only = [AttributePath.from_string("model_a.name")]
    join_tree = registry.dag.find_best_join_tree(references_a_only)
    assert len(join_tree) == 1, f"Expected tree with 1 node, got {len(join_tree)}"
    assert (
        join_tree.root == "model_a"
    ), f"Expected root to be model_a, got {join_tree.root}"

    # Test 2: Only need D
    references_d_only = [AttributePath.from_string("model_d.value")]
    join_tree = registry.dag.find_best_join_tree(references_d_only)
    assert (
        len(join_tree) == 1
    ), f"Expected tree with 1 node (just D), got {len(join_tree)}"
    assert (
        join_tree.root == "model_d"
    ), f"Expected root to be model_d, got {join_tree.root}"

    # Test 3: Two models with direct relationship - A and B
    references_a_b = [
        AttributePath.from_string("model_a.name"),
        AttributePath.from_string("model_b.name"),
    ]
    join_tree = registry.dag.find_best_join_tree(references_a_b)
    assert len(join_tree) == 2, f"Expected tree with 2 nodes, got {len(join_tree)}"
    assert join_tree.root in [
        "model_a",
        "model_b",
    ], f"Expected root to be model_a or model_b, got {join_tree.root}"

    # Test 4: Path through A->...->D
    references_a_b_d = [
        AttributePath.from_string("model_a.name"),
        AttributePath.from_string("model_d.value"),
    ]
    join_tree = registry.dag.find_best_join_tree(references_a_b_d)
    expected_models = {"model_a", "model_d"}
    actual_models = set(join_tree.parents.keys())
    assert expected_models.issubset(
        actual_models
    ), f"Expected models {expected_models} to be subset of {actual_models}"

    # Test 5: Verify that find_best_join_tree finds the minimal tree when multiple options exist
    references_both_paths = [
        AttributePath.from_string("model_a.name"),
        AttributePath.from_string("model_b.name"),
        AttributePath.from_string("model_d.value"),
    ]
    expected_models = {"model_a", "model_b", "model_d"}
    join_tree = registry.dag.find_best_join_tree(references_both_paths)
    actual_models = set(join_tree.parents.keys())
    assert expected_models.issubset(
        actual_models
    ), f"Expected models {expected_models} to be subset of {actual_models}"


def test_dag_find_best_join_tree_comparison():
    """Test that find_best_join_tree chooses the smaller of two possible trees."""

    registry = Registry()

    # Create a simple linear chain: A -> B -> C
    model_a = Model(
        name="model_a",
        table="table_a",
        relationships=[
            Relationship(
                name="to_b",
                ref_model="model_b",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="b_id",
                ref_key="id",
            )
        ],
        dimensions=[
            Dimension(name="id", description="A's ID"),
            Dimension(name="name", description="A's name"),
        ],
        measures=[],
    )

    model_b = Model(
        name="model_b",
        table="table_b",
        relationships=[
            Relationship(
                name="to_c",
                ref_model="model_c",
                type=RelationshipType.MANY_TO_ONE,
                source_foreign_key="c_id",
                ref_key="id",
            )
        ],
        dimensions=[
            Dimension(name="id", description="B's ID"),
            Dimension(name="name", description="B's name"),
        ],
        measures=[],
    )

    model_c = Model(
        name="model_c",
        table="table_c",
        relationships=[],
        dimensions=[
            Dimension(name="id", description="C's ID"),
            Dimension(name="value", description="C's value"),
        ],
        measures=[],
    )

    # Register all models
    registry.register(model_a)
    registry.register(model_b)
    registry.register(model_c)

    # Test that when we only need B and C, we get a tree rooted at B or C (not A)
    references_b_c = [
        AttributePath.from_string("model_b.name"),
        AttributePath.from_string("model_b.to_c->model_c.value"),
    ]

    join_tree = registry.dag.find_best_join_tree(references_b_c)

    # Should only include B and C, not A
    assert (
        len(join_tree) == 2
    ), f"Expected tree with 2 nodes (B,C), got {len(join_tree)}"
    assert (
        "model_a" not in join_tree.parents
    ), f"Tree should not include model_a: {join_tree.parents}"
    assert (
        "model_b" in join_tree.parents
    ), f"Tree should include model_b: {join_tree.parents}"
    assert (
        "model_c" in join_tree.parents
    ), f"Tree should include model_c: {join_tree.parents}"

    print("✓ find_best_join_tree correctly excludes unnecessary models")


def test_dag_find_best_join_tree_no_path():
    """Test that find_best_join_tree raises appropriate error when no path exists."""
    registry = Registry()

    # Create two isolated models with no connections
    model_a = Model(
        name="model_a",
        table="table_a",
        relationships=[],
        dimensions=[
            Dimension(name="id", description="A's ID"),
            Dimension(name="name", description="A's name"),
        ],
        measures=[],
    )

    model_b = Model(
        name="model_b",
        table="table_b",
        relationships=[],
        dimensions=[
            Dimension(name="id", description="B's ID"),
            Dimension(name="name", description="B's name"),
        ],
        measures=[],
    )

    registry.register(model_a)
    registry.register(model_b)

    # Try to find a join tree that requires both isolated models
    references = [
        AttributePath.from_string("model_a.name"),
        AttributePath.from_string("model_b.name"),
    ]

    # This should raise ModelHasNoJoinPath exception
    try:
        registry.dag.find_best_join_tree(references)
        assert False, "Expected ModelHasNoJoinPath exception"
    except ModelHasNoJoinPath as e:
        assert "No join tree found" in str(e)
        print(
            "✓ find_best_join_tree correctly raises exception for disconnected models"
        )
