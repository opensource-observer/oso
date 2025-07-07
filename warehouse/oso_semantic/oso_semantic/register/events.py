import textwrap

from ..definition import (
    Dimension,
    Measure,
    Model,
    Registry,
    Relationship,
    RelationshipType,
)


def register_events(registry: Registry, catalog_name: str = "iceberg"):
    # ============================================"
    # EVENTS
    # ============================================"

    registry.register(
        Model(
            name="event_types",
            table=f"{catalog_name}.oso.event_types_v1",
            description=textwrap.dedent(
                """
                The event_types_v1 table contains distinct event types from various sources, 
                such as GitHub, blockchain, and funding events. This table is used to enumerate 
                different types of events that occur across the open source ecosystem.
                """
            ),
            dimensions=[
                Dimension(
                    name="event_type",
                    description="The unique identifier for the event type",
                    column_name="event_type",
                ),
            ],
            primary_key="event_type",
            measures=[
                Measure(
                    name="count",
                    description="The number of distinct event types",
                    query="COUNT(*)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="int_events__github",
            table=f"{catalog_name}.oso.int_events__github",
            description=textwrap.dedent(
                """
                GitHub events aggregated daily. This includes all types of GitHub activity
                such as commits, pull requests, issues, stars, forks, and more.
                """
            ),
            dimensions=[
                Dimension(
                    name="bucket_day",
                    description="The day the event occurred",
                    column_name="bucket_day",
                ),
                Dimension(
                    name="event_type",
                    description="The type of the GitHub event",
                    column_name="event_type",
                ),
                Dimension(
                    name="event_source",
                    description="The source of the event (always GITHUB)",
                    column_name="event_source",
                ),
                Dimension(
                    name="amount",
                    description="The amount or count of the event",
                    column_name="amount",
                ),
                Dimension(
                    name="month",
                    description="The month the event occurred",
                    query="DATE_TRUNC('month', self.bucket_day)",
                ),
                Dimension(
                    name="year",
                    description="The year the event occurred",
                    query="DATE_TRUNC('year', self.bucket_day)",
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of events",
                    query="COUNT(*)",
                ),
                Measure(
                    name="total_amount",
                    description="The total amount of events",
                    query="SUM(self.amount)",
                ),
                Measure(
                    name="avg_amount",
                    description="The average amount of events",
                    query="AVG(self.amount)",
                ),
            ],
            time_column="bucket_day",
            relationships=[
                Relationship(
                    name="from",
                    description="The artifact from which the event occurred",
                    source_foreign_key="from_artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    name="to",
                    description="The artifact to which the event occurred",
                    source_foreign_key="to_artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="int_events_daily__blockchain",
            table=f"{catalog_name}.oso.int_events_daily__blockchain",
            description=textwrap.dedent(
                """
                Blockchain events aggregated daily. This includes various blockchain activities
                such as transactions, token transfers, contract interactions, and more.
                """
            ),
            dimensions=[
                Dimension(
                    name="bucket_day",
                    description="The day the event occurred",
                    column_name="bucket_day",
                ),
                Dimension(
                    name="event_type",
                    description="The type of the blockchain event",
                    column_name="event_type",
                ),
                Dimension(
                    name="event_source",
                    description="The source blockchain",
                    column_name="event_source",
                ),
                Dimension(
                    name="amount",
                    description="The amount or count of the event",
                    column_name="amount",
                ),
                Dimension(
                    name="month",
                    description="The month the event occurred",
                    query="DATE_TRUNC('month', self.bucket_day)",
                ),
                Dimension(
                    name="year",
                    description="The year the event occurred",
                    query="DATE_TRUNC('year', self.bucket_day)",
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of events",
                    query="COUNT(*)",
                ),
                Measure(
                    name="total_amount",
                    description="The total amount of events",
                    query="SUM(self.amount)",
                ),
                Measure(
                    name="avg_amount",
                    description="The average amount of events",
                    query="AVG(self.amount)",
                ),
            ],
            time_column="bucket_day",
            relationships=[
                Relationship(
                    name="from",
                    description="The artifact from which the event occurred",
                    source_foreign_key="from_artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    name="to",
                    description="The artifact to which the event occurred",
                    source_foreign_key="to_artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="int_events_daily__funding",
            table=f"{catalog_name}.oso.int_events_daily__funding",
            description=textwrap.dedent(
                """
                Funding events aggregated daily. This includes funding activities from various
                sources such as Gitcoin, Open Collective, and other funding platforms.
                """
            ),
            dimensions=[
                Dimension(
                    name="bucket_day",
                    description="The day the event occurred",
                    column_name="bucket_day",
                ),
                Dimension(
                    name="event_type",
                    description="The type of the funding event",
                    column_name="event_type",
                ),
                Dimension(
                    name="event_source",
                    description="The source of the funding",
                    column_name="event_source",
                ),
                Dimension(
                    name="amount",
                    description="The funding amount",
                    column_name="amount",
                ),
                Dimension(
                    name="month",
                    description="The month the event occurred",
                    query="DATE_TRUNC('month', self.bucket_day)",
                ),
                Dimension(
                    name="year",
                    description="The year the event occurred",
                    query="DATE_TRUNC('year', self.bucket_day)",
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of events",
                    query="COUNT(*)",
                ),
                Measure(
                    name="total_amount",
                    description="The total amount of events",
                    query="SUM(self.amount)",
                ),
                Measure(
                    name="avg_amount",
                    description="The average amount of events",
                    query="AVG(self.amount)",
                ),
            ],
            time_column="bucket_day",
            relationships=[
                Relationship(
                    name="from",
                    description="The artifact from which the event occurred",
                    source_foreign_key="from_artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    name="to",
                    description="The artifact to which the event occurred",
                    source_foreign_key="to_artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )
