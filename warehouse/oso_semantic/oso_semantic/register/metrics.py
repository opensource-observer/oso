import textwrap

from ..definition import (
    Dimension,
    Measure,
    Model,
    Registry,
    Relationship,
    RelationshipType,
)


def register_metrics(registry: Registry, catalog_name: str = "iceberg"):
    # ============================================"
    # METRICS MODELS
    # ============================================"

    registry.register(
        Model(
            name="metrics",
            table=f"{catalog_name}.oso.metrics_v0",
            description=textwrap.dedent(
                """
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
                """
            ),
            dimensions=[
                Dimension(
                    name="metric_id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="metric_source",
                    description="The source of the metric, typically OSO",
                    column_name="metric_source",
                ),
                Dimension(
                    name="metric_namespace",
                    description="The namespace grouping of the metric",
                    column_name="metric_namespace",
                ),
                Dimension(
                    name="metric_name",
                    description="The name of the metric",
                    column_name="metric_name",
                ),
                Dimension(
                    name="display_name",
                    description="A human-readable name for the metric",
                    column_name="display_name",
                ),
                Dimension(
                    name="description",
                    description="A description of the metric",
                    column_name="description",
                ),
                Dimension(
                    name="rendered_sql",
                    description="The SQL query used to compute the metric",
                    column_name="rendered_sql",
                ),
                Dimension(
                    name="sql_source_path",
                    description="The path to the SQL file that defines the metric",
                    column_name="sql_source_path",
                ),
                Dimension(
                    name="aggregation_function",
                    description="The aggregation function used for the metric",
                    column_name="aggregation_function",
                ),
            ],
            primary_key="metric_id",
            measures=[
                Measure(
                    name="count",
                    description="The number of metrics",
                    query="COUNT(self.metric_id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct metrics",
                    query="COUNT(DISTINCT self.metric_id)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="timeseries_metrics_by_artifact",
            table=f"{catalog_name}.oso.timeseries_metrics_by_artifact_v0",
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
                    name="metric_id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="artifact_id",
                    description="The unique identifier of the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="sample_date",
                    description="The date when the metric was sampled",
                    column_name="sample_date",
                ),
                Dimension(
                    name="amount",
                    description="The value of the metric",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of the metric",
                    column_name="unit",
                ),
            ],
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
                Measure(
                    name="count",
                    description="The count of metric records",
                    query="COUNT(*)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metrics",
                    ref_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="timeseries_metrics_by_project",
            table=f"{catalog_name}.oso.timeseries_metrics_by_project_v0",
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
                    name="metric_id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="project_id",
                    description="The unique identifier of the project",
                    column_name="project_id",
                ),
                Dimension(
                    name="sample_date",
                    description="The date when the metric was sampled",
                    column_name="sample_date",
                ),
                Dimension(
                    name="amount",
                    description="The value of the metric",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of the metric",
                    column_name="unit",
                ),
            ],
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
                Measure(
                    name="count",
                    description="The count of metric records",
                    query="COUNT(*)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="projects",
                    ref_key="project_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metrics",
                    ref_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="timeseries_metrics_by_collection",
            table=f"{catalog_name}.oso.timeseries_metrics_by_collection_v0",
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
                    name="metric_id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="collection_id",
                    description="The unique identifier of the collection",
                    column_name="collection_id",
                ),
                Dimension(
                    name="sample_date",
                    description="The date when the metric was sampled",
                    column_name="sample_date",
                ),
                Dimension(
                    name="amount",
                    description="The value of the metric",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of the metric",
                    column_name="unit",
                ),
            ],
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
                Measure(
                    name="count",
                    description="The count of metric records",
                    query="COUNT(*)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="collection_id",
                    ref_model="collections",
                    ref_key="collection_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metrics",
                    ref_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="key_metrics_by_artifact",
            table=f"{catalog_name}.oso.key_metrics_by_artifact_v0",
            description=textwrap.dedent(
                """
                Key metrics for artifacts. Each row represents the latest value of 
                a specific metric for a given artifact.
                """
            ),
            dimensions=[
                Dimension(
                    name="metric_id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="artifact_id",
                    description="The unique identifier of the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="sample_date",
                    description="The date when the metric was sampled",
                    column_name="sample_date",
                ),
                Dimension(
                    name="amount",
                    description="The value of the metric for the artifact",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of measurement for the metric",
                    column_name="unit",
                ),
            ],
            primary_key=["metric_id", "artifact_id"],
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
                Measure(
                    name="count",
                    description="The count of metric records",
                    query="COUNT(*)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metrics",
                    ref_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="key_metrics_by_project",
            table=f"{catalog_name}.oso.key_metrics_by_project_v0",
            description=textwrap.dedent(
                """
                Key metrics for projects. Each row represents the latest value of 
                a specific metric for a given project.
                """
            ),
            dimensions=[
                Dimension(
                    name="metric_id",
                    description="The unique identifier of the metric",
                    column_name="metric_id",
                ),
                Dimension(
                    name="project_id",
                    description="The unique identifier of the project",
                    column_name="project_id",
                ),
                Dimension(
                    name="sample_date",
                    description="The date when the metric was sampled",
                    column_name="sample_date",
                ),
                Dimension(
                    name="amount",
                    description="The value of the metric for the project",
                    column_name="amount",
                ),
                Dimension(
                    name="unit",
                    description="The unit of measurement for the metric",
                    column_name="unit",
                ),
            ],
            primary_key=["metric_id", "project_id"],
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
                Measure(
                    name="count",
                    description="The count of metric records",
                    query="COUNT(*)",
                ),
            ],
            relationships=[
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="projects",
                    ref_key="project_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="metric_id",
                    ref_model="metrics",
                    ref_key="metric_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )
