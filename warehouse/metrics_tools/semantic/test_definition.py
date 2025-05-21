from metrics_tools.semantic.definition import AttributeReference


def test_attribute_reference_traversal():

    ref1 = AttributeReference.from_string("a.b->c.d->e.f")
    ref2 = AttributeReference(ref=["a.b", "c.d", "e.f"])
    ref3 = AttributeReference(ref=["a.b", "c.d", "x.y"])
    ref4 = AttributeReference(ref=["a.g", "c.d", "e.f"])
    assert ref1 == ref2
    assert ref1 != ref3

    t1 = ref1.traverser()
    t2 = ref2.traverser()

    assert t1.current_model_name == t2.current_model_name
    assert t1.current_table_alias == t2.current_table_alias

    while t1.next() and t2.next():
        assert t1.current_model_name == t2.current_model_name
        assert t1.current_table_alias == t2.current_table_alias
        assert t1.current_column == t2.current_column
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

    assert t1.current_column.name != t3.current_column.name
    assert t1.alias("foo") == t3.alias("foo")

    while t1.prev():
        pass

    t4 = ref4.traverser()

    assert t1.alias("foo") == t4.alias("foo")

    t1.next()
    t4.next()

    assert t1.alias("foo") != t4.alias("foo")



# def test_semantic_model_shortest_path():
#     registry = setup_registry()

#     assert registry.dag.join_paths("event", "artifact") == (
#         ["event", "artifact"],
#         ["artifact"],
#     )

#     assert registry.dag.join_paths("artifact", "event") == (
#         ["artifact"],
#         ["event", "artifact"],
#     )

#     assert registry.dag.join_paths("artifact", "project") == (
#         ["artifact", "project"],
#         ["project"],
#     )

#     assert registry.dag.join_paths("event", "collection") == (
#         ["event", "artifact", "project", "collection"],
#         ["collection"],
#     )

#     to_artifact_ref = registry.get_model("event").get_relationship(model_ref="artifact", name="to")
#     from_artifact_ref =  registry.get_model("event").get_relationship(model_ref="artifact", name="from")

#     assert to_artifact_ref.model_ref == "artifact"
#     assert to_artifact_ref.name == "to"
#     assert to_artifact_ref.foreign_key_column == "to_artifact_id"
#     assert from_artifact_ref.model_ref == "artifact"
#     assert from_artifact_ref.name == "from"
#     assert from_artifact_ref.foreign_key_column == "from_artifact_id"

#     query = SemanticQuery(
#         columns=[
#             exp.to_column("event.time"),
#             exp.to_column("event.event_source"),
#             [exp.to_column("event.from"), exp.to_column("artifact.name")],
#             #[exp.to_column("event.to"), exp.to_column("collection.name")],
#         ]
#     )
    

#     assert len(registry.join_relationships("event", "collection")) == 3

#     print(registry.query(query).sql(dialect="duckdb", pretty=True))
#     assert False