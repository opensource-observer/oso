"""
Semantic models

Need a semantic joiner
Need a parameterizing factory

SemanticQuery(
    columns=[
        "@source.time",
        "@source.to_artifact_id",
        "@source.from_artifact_id",
        "@source.event_type",
        "@source.event_source",
        "@source.event_source_id",
        "@source.to_artifact_name",
        "@source.to_artifact_namespace",
        "@source.to_artifact_type",
        "@source.to_artifact_source_id",
        "@source.from_artifact_name",
        "@source.from_artifact_namespace",
        "@source.from_artifact_type",
        "@source.from_artifact_source_id",
        "SUM(@source.amount)"
    ],
    filters=["@source.to_artifact_id IN (SELECT @source.artifact_id FROM oso.int_repositories)",],
)

"""


def int_events_daily_factory(source: str):
    """Generates a SQL query to create a daily events table."""
    pass
