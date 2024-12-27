from metrics_tools.semantic.definition import (
    Dimension,
    Model,
    Reference,
    ReferenceType,
    Registry,
    SemanticQuery,
)
from sqlglot import exp


def setup_registry():
    registry = Registry()

    registry.register(
        Model(
            name="collection",
            description="A collection of projects",
            dimensions=[
                Dimension(name="id"),
                Dimension(name="name"),
            ],
            primary_key="id",
        )
    )

    registry.register(
        Model(
            name="project",
            description="A project",
            dimensions=[
                Dimension(name="id"),
                Dimension(name="name"),
                Dimension(name="portfolio_id"),
            ],
            primary_key="id",
            references=[
                Reference(
                    model_ref="collection",
                    type=ReferenceType.INNER,
                    via="projects_by_collection_v1",
                    self_key_column="project_id",
                    foreign_key_column="collection_id",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="artifact",
            description="An artifact",
            dimensions=[
                Dimension(name="id"),
                Dimension(name="name"),
                Dimension(name="email"),
            ],
            primary_key="id",
            references=[
                Reference(
                    model_ref="project",
                    type=ReferenceType.INNER,
                    via="artifacts_by_project_v1",
                    self_key_column="artifact_id",
                    foreign_key_column="project_id",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="event",
            description="An event",
            dimensions=[
                Dimension(
                    name="time",
                    description="The day the event occurred",
                ),
                Dimension(
                    name="event_source",
                    description="The source of the event",
                ),
                Dimension(
                    name="event_type",
                    description="The type of the event",
                ),
                Dimension(
                    name="event_id",
                    description="The unique identifier of the event",
                ),
                Dimension(
                    name="amount",
                    description="The amount of the event",
                ),
            ],
            time_column="time",
            primary_key="id",
            references=[
                Reference(
                    name="to",
                    model_ref="artifact",
                    type=ReferenceType.INNER,
                    foreign_key_column="to_artifact_id",
                ),
                Reference(
                    name="from",
                    model_ref="artifact",
                    type=ReferenceType.INNER,
                    foreign_key_column="from_artifact_id",
                ),
            ],
        )
    )
    registry.complete()
    return registry


def test_semantic_model_shortest_path():
    registry = setup_registry()

    assert registry.dag.join_paths("event", "artifact") == (
        ["event", "artifact"],
        ["artifact"],
    )

    assert registry.dag.join_paths("artifact", "event") == (
        ["artifact"],
        ["event", "artifact"],
    )

    assert registry.dag.join_paths("artifact", "project") == (
        ["artifact", "project"],
        ["project"],
    )

    assert registry.dag.join_paths("event", "collection") == (
        ["event", "artifact", "project", "collection"],
        ["collection"],
    )

    to_artifact_ref = registry.get_model("event").get_reference(model_ref="artifact", name="to")
    from_artifact_ref =  registry.get_model("event").get_reference(model_ref="artifact", name="from")

    assert to_artifact_ref.model_ref == "artifact"
    assert to_artifact_ref.name == "to"
    assert to_artifact_ref.foreign_key_column == "to_artifact_id"
    assert from_artifact_ref.model_ref == "artifact"
    assert from_artifact_ref.name == "from"
    assert from_artifact_ref.foreign_key_column == "from_artifact_id"

    query = SemanticQuery(
        columns=[
            exp.to_column("event.time"),
            exp.to_column("event.event_source"),
            [exp.to_column("event.from"), exp.to_column("artifact.name")],
            #[exp.to_column("event.to"), exp.to_column("collection.name")],
        ]
    )
    

    assert len(registry.join_references("event", "collection")) == 3

    print(registry.query(query).sql(dialect="duckdb", pretty=True))
    assert False