# An example semantic model for testing
from .definition import (
    Dimension,
    Metric,
    Model,
    Registry,
    Relationship,
    RelationshipType,
)


def setup_registry():
    registry = Registry()

    registry.register(
        Model(
            name="collection",
            table="oso.collections_v1",
            description="A collection of projects",
            dimensions=[
                Dimension(name="id", column_name="collection_id"),
                Dimension(name="name", column_name="collection_name"),
            ],
            primary_key="collection_id",
            metrics=[
                Metric(
                    name="count",
                    description="The number of collections",
                    query="COUNT(self.id)",
                ),
                # Metric(
                #     name="number_of_projects",
                #     description="The number of related projects in the collection",
                #     query="COUNT(project.id)",
                # )
            ]
        )
    )

    registry.register(
        Model(
            name="project",
            table="oso.projects_v1",
            description="A project",
            dimensions=[
                Dimension(
                    name="id", 
                    description="The unique identifier of the project",
                    column_name="project_id"
                ),
                Dimension(
                    name="name",
                    description="The name of the project",
                    column_name="project_name"
                ),
            ],
            primary_key="project_id",
            references=[
                Relationship(
                    model_ref="collection",
                    type=RelationshipType.MANY_TO_MANY,
                    join_table="oso.projects_by_collection_v1",
                    self_key_column="project_id",
                    foreign_key_column="collection_id",
                ),
            ],
            metrics=[
                Metric(
                    name="count",
                    description="The number of projects",
                    query="COUNT(self.id)",
                ),
                # Metric(
                #     name="number_of_artifacts",
                #     description="The number of related artifacts in the project",
                #     query="COUNT(artifact.id)",
                # )
            ]
        )
    )

    registry.register(
        Model(
            name="artifact",
            table="oso.artifacts_v1",
            description="An artifact",
            dimensions=[
                Dimension(
                    name="id", 
                    description="The unique identifier of the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="name",
                    description="The name of the artifact",
                    column_name="artifact_name"
                ),
                Dimension(
                    name="url",
                    description="The URL of the artifact",
                    column_name="artifact_url"
                ),
            ],
            primary_key="artifact_id",
            references=[
                Relationship(
                    model_ref="project",
                    type=RelationshipType.MANY_TO_MANY,
                    join_table="oso.artifacts_by_project_v1",
                    self_key_column="artifact_id",
                    foreign_key_column="project_id",
                ),
            ],
            metrics=[
                Metric(
                    name="count",
                    description="The number of artifacts",
                    query="COUNT(self.id)",
                ),
            ]
        )
    )

    registry.register(
        Model(
            name="github_event",
            table="oso.int_events__github",
            description="An event",
            dimensions=[
                Dimension(
                    name="time",
                    description="The day the event occurred",
                ),
                Dimension(
                    name="month",
                    description="The month the event occurred",
                    query="DATE_TRUNC('month', self.time::date)",
                ),
                Dimension(
                    name="day",
                    description="The day the event occurred",
                    query="DATE_TRUNC('day', self.time::date)",
                ),
                Dimension(
                    name="year",
                    description="The year the event occurred",
                    query="DATE_TRUNC('year', self.time::date)",
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
                    name="id",
                    description="The unique identifier of the event",
                ),
                Dimension(
                    name="amount",
                    description="The amount of the event",
                ),
                Dimension(
                    name="event_type_classification",
                    description="The classification of the event type",
                    query="CASE WHEN self.event_type = 'COMMIT' THEN 'COMMIT' ELSE 'OTHER' END",
                )
            ],
            metrics=[
                Metric(
                    name="count",
                    description="The number of events",
                    query="COUNT(self.id)",
                ),
                Metric(
                    name="total_amount",
                    description="The total amount of events",
                    query="SUM(self.amount)",
                ),
            ],
            time_column="time",
            primary_key="event_id",
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