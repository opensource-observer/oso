from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class IntEventsBlockchain(BaseModel):
    time: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    to_artifact_id: str | None = Column("VARCHAR")
    from_artifact_id: str | None = Column("VARCHAR")
    event_type: str | None = Column("VARCHAR")
    event_source_id: str | None = Column("VARCHAR")
    event_source: str | None = Column("VARCHAR")
    to_artifact_name: str | None = Column("VARCHAR")
    to_artifact_namespace: str | None = Column("VARCHAR")
    to_artifact_type: str | None = Column("VARCHAR")
    to_artifact_source_id: str | None = Column("VARCHAR")
    from_artifact_name: str | None = Column("VARCHAR")
    from_artifact_namespace: str | None = Column("VARCHAR")
    from_artifact_type: str | None = Column("VARCHAR")
    from_artifact_source_id: str | None = Column("VARCHAR")
    amount: float | None = Column("DOUBLE")


seed = SeedConfig(
    catalog="bigquery",
    schema="oso",
    table="int_events__blockchain",
    base=IntEventsBlockchain,
    rows=[
        IntEventsBlockchain(
            time=datetime.now(),
            to_artifact_id="artifact1",
            from_artifact_id="artifact2",
            event_type="type1",
            event_source_id="source1",
            event_source="sourceA",
            to_artifact_name="name1",
            to_artifact_namespace="namespace1",
            to_artifact_type="typeA",
            to_artifact_source_id="sourceID1",
            from_artifact_name="name2",
            from_artifact_namespace="namespace2",
            from_artifact_type="typeB",
            from_artifact_source_id="sourceID2",
            amount=100.0,
        ),
        IntEventsBlockchain(
            time=datetime.now(),
            to_artifact_id="artifact3",
            from_artifact_id="artifact4",
            event_type="type2",
            event_source_id="source2",
            event_source="sourceB",
            to_artifact_name="name3",
            to_artifact_namespace="namespace3",
            to_artifact_type="typeC",
            to_artifact_source_id="sourceID3",
            from_artifact_name="name4",
            from_artifact_namespace="namespace4",
            from_artifact_type="typeD",
            from_artifact_source_id="sourceID4",
            amount=200.0,
        ),
    ],
)
