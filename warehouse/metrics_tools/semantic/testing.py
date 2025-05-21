# An example semantic model for testing
from .definition import Dimension, Model, Registry, Relationship, RelationshipType


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
                Relationship(
                    model_ref="collection",
                    type=RelationshipType.MANY_TO_MANY,
                    join_table="projects_by_collection_v1",
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
                Relationship(
                    model_ref="project",
                    type=RelationshipType.MANY_TO_MANY,
                    join_table="artifacts_by_project_v1",
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
                Relationship(
                    name="to",
                    model_ref="artifact",
                    type=RelationshipType.MANY_TO_ONE,
                    foreign_key_column="to_artifact_id",
                ),
                Relationship(
                    name="from",
                    model_ref="artifact",
                    type=RelationshipType.MANY_TO_ONE,
                    foreign_key_column="from_artifact_id",
                ),
            ],
        )
    )
    registry.complete()
    return registry