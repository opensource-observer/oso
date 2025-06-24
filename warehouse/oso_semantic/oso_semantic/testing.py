# An example semantic model for testing
import textwrap

from .definition import (
    Dimension,
    Measure,
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
            description=textwrap.dedent("""
                A collection is a group of related projects. A collection is an
                arbitrary grouping of projects. Sometimes these groupings are
                used to group things together by some common dependency tree or
                some specific community known to OSO.
            """),
            dimensions=[
                Dimension(
                    name="id",
                    description="The unique identifier of the collection",
                    column_name="collection_id",
                ),
                Dimension(
                    name="name",
                    description="The name of the collection",
                    column_name="collection_name",
                ),
            ],
            primary_key="collection_id",
            measures=[
                Measure(
                    name="count",
                    description="The number of collections",
                    query="COUNT(self.id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct collections",
                    query="COUNT(DISTINCT self.id)",
                ),
                # Metric(
                #     name="number_of_projects",
                #     description="The number of related projects in the collection",
                #     query="COUNT(project.id)",
                # )
            ],
        )
    )

    registry.register(
        Model(
            name="project",
            table="oso.projects_v1",
            description=textwrap.dedent(
                """
                A project is a collection of related artifacts. A project is
                usually, but not limited to, some kind of organization, company,
                or group that controls a set of artifacts.
            """
            ),
            dimensions=[
                Dimension(
                    name="id",
                    description="The unique identifier of the project",
                    column_name="project_id",
                ),
                Dimension(
                    name="name",
                    description="The name of the project",
                    column_name="project_name",
                ),
            ],
            primary_key="project_id",
            relationships=[
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="projects_by_collection",
                    ref_foreign_key="project_id",
                    type=RelationshipType.ONE_TO_MANY,
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of projects",
                    query="COUNT(self.id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct projects",
                    query="COUNT(DISTINCT self.id)",
                ),
                # Metric(
                #     name="number_of_artifacts",
                #     description="The number of related artifacts in the project",
                #     query="COUNT(artifact.id)",
                # )
            ],
        )
    )

    registry.register(
        Model(
            name="projects_by_collection",
            table="oso.projects_by_collection_v1",
            description=textwrap.dedent(
                """
                The join table between projects and collections. This table
                represents the many-to-many relationship between projects and
                collections.
            """
            ),
            dimensions=[
                Dimension(
                    name="project_id",
                    description="The unique identifier of the project",
                    column_name="project_id",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="collection_id",
                    ref_model="collection",
                    ref_foreign_key="collection_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="artifact",
            table="oso.artifacts_v1",
            description=textwrap.dedent(
                """
                An artifact. This is the smallest atom of an acting entity in
                OSO. Artifacts are usually repositories, blockchain addresses,
                or some representation of a user. Artifacts do not generally
                represent a group of any kind, but rather a single entity.
            """
            ),
            dimensions=[
                Dimension(
                    name="id",
                    description="The unique identifier of the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="name",
                    description="The name of the artifact",
                    column_name="artifact_name",
                ),
                Dimension(
                    name="url",
                    description="The URL of the artifact",
                    column_name="artifact_url",
                ),
            ],
            primary_key="artifact_id",
            relationships=[
                Relationship(
                    source_foreign_key="artifact_id",
                    ref_model="artifacts_by_project",
                    ref_foreign_key="artifact_id",
                    type=RelationshipType.ONE_TO_MANY,
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of artifacts",
                    query="COUNT(self.id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct artifacts",
                    query="COUNT(DISTINCT self.id)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="artifacts_by_project",
            table="oso.artifacts_by_project_v1",
            description=textwrap.dedent(
                """
                The join table between artifacts and projects. This table
                represents the many-to-many relationship between artifacts and
                projects.
            """
            ),
            dimensions=[
                Dimension(
                    name="artifact_id",
                    description="The unique identifier of the artifact",
                    column_name="artifact_id",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="project",
                    ref_foreign_key="project_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="github_event",
            table="oso.int_events__github",
            description=textwrap.dedent(
                """
                A github event. This could be any event that occurs on github.
            """
            ),
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
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of events",
                    query="COUNT(self.id)",
                ),
                Measure(
                    name="total_amount",
                    description="The total amount of events",
                    query="SUM(self.amount)",
                ),
            ],
            time_column="time",
            primary_key="event_id",
            relationships=[
                Relationship(
                    name="to",
                    description="The artifact to which the event occurred",
                    source_foreign_key="to_artifact_id",
                    ref_model="artifact",
                    ref_foreign_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    name="from",
                    description="The artifact from which the event occurred",
                    source_foreign_key="from_artifact_id",
                    ref_model="artifact",
                    ref_foreign_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="metrics",
            table="oso.metrics_v0",
            description=textwrap.dedent("""
                Each row represents metadata about a unique metric. This data can be
                used to analyze trends and performance indicators across various
                open source projects, supporting business decisions around developer
                engagement, funding, and project health. This table is necessary for
                doing keyword searches to discover relevant metrics ids, and joining
                on the other metrics tables (eg, key_metrics_by_project and
                timeseries_metrics_by_project). Business questions that can be
                answered include: Which daily metrics are available for "BASE"? What
                are the available metric ids for GITHUB_stars? Which metrics are
                relevant to contract artifacts on "OPTIMISM"?'
            """),
            dimensions=[
                Dimension(
                    name="id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="name",
                    description="The name of the metric",
                    column_name="metric_name",
                ),
                Dimension(
                    name="description",
                    description="A description of the metric",
                    column_name="metric_description",
                ),
                Dimension(
                    name="source",
                    description="The source of the metric",
                    column_name="metric_source",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="timeseries_metrics_by_artifact",
            table="oso.timeseries_metrics_by_artifact_v0",
            description=textwrap.dedent(
                """
                Many-to-many table between metrics, artifacts, and dates. Each row
                represents the value of a specific metric for a given artifact on a
                particular date, capturing how that metric changes over time. This
                is one of the most important models for OSO and should be used
                frequently in analysis. However, in order to use this table
                correctly, it is necessary to join on metrics and artifacts
                (or other artifact-related tables). Business questions that can be
                answered include: Which artifacts have the most active developers?
                How many forks does this artifact have?
            """
            ),
            dimensions=[
                Dimension(
                    name="sample_date",
                    column_name="month",
                ),
                Dimension(
                    name="amount",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of the metric",
                    column_name="unit",
                ),
            ],
            # Need to support composite primary keys
            primary_key=["metric_id", "artifact_id", "sample_date"],
            measures=[
                Measure(
                    name="sum",
                    description="The total sum of artifact metrics",
                    query="SUM(self.amount)",
                ),
                Measure(
                    name="avg",
                    description="The average of artifact metrics",
                    query="AVG(self.amount)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="artifact_id",
                    ref_model="artifact",
                    ref_foreign_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metric",
                    ref_foreign_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="timeseries_metrics_by_project",
            table="oso.timeseries_metrics_by_project_v0",
            description=textwrap.dedent(
                """
                Many-to-many table between metrics, projects, and dates. Each row
                represents the value of a specific metric for a given project on a
                particular date, capturing how that metric changes over time. This
                is one of the most important models for OSO and should be used
                frequently in analysis. However, in order to use this table
                correctly, it is necessary to join on metrics and projects
                (or other project-related tables). Business questions that can be
                answered include: Which projects have the most active developers?
                How many forks does this project have?
            """
            ),
            dimensions=[
                Dimension(
                    name="sample_date",
                    column_name="month",
                ),
                Dimension(
                    name="amount",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of the metric",
                    column_name="unit",
                ),
            ],
            # Need to support composite primary keys
            primary_key=["metric_id", "project_id", "sample_date"],
            measures=[
                Measure(
                    name="sum",
                    description="The total sum of project metrics",
                    query="SUM(self.amount)",
                ),
                Measure(
                    name="avg",
                    description="The average of project metrics",
                    query="AVG(self.amount)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="project",
                    ref_foreign_key="project_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metric",
                    ref_foreign_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="timeseries_metrics_by_collection",
            table="oso.timeseries_metrics_by_collection_v0",
            description=textwrap.dedent(
                """
                Many-to-many table between metrics, collections, and dates. Each row
                represents the value of a specific metric for a given collection on a
                particular date, capturing how that metric changes over time. This
                is one of the most important models for OSO and should be used
                frequently in analysis. However, in order to use this table
                correctly, it is necessary to join on metrics and collections
                (or other collection-related tables). Business questions that can be
                answered include: Which collections have the most active developers?
                How many forks does this collection have?
            """
            ),
            dimensions=[
                Dimension(
                    name="sample_date",
                    column_name="month",
                ),
                Dimension(
                    name="amount",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of the metric",
                    column_name="unit",
                ),
            ],
            # Need to support composite primary keys
            primary_key=["metric_id", "collection_id", "sample_date"],
            measures=[
                Measure(
                    name="sum",
                    description="The total sum of collection metrics",
                    query="SUM(self.amount)",
                ),
                Measure(
                    name="avg",
                    description="The average of collection metrics",
                    query="AVG(self.amount)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="collection_id",
                    ref_model="collection",
                    ref_foreign_key="collection_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metric",
                    ref_foreign_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.complete()
    return registry
