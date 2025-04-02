from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from pydantic import BaseModel, Field


class IntEventsBlockchain(BaseModel):
    time: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )
    to_artifact_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    from_artifact_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    event_type: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    event_source_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    event_source: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    to_artifact_name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    to_artifact_namespace: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    to_artifact_type: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    to_artifact_source_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    from_artifact_name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    from_artifact_namespace: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    from_artifact_type: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    from_artifact_source_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    amount: float | None = Field(json_schema_extra={"sql": "DOUBLE"})


async def seed(loader: DestinationLoader):
    await loader.create_table("oso.int_events__blockchain", IntEventsBlockchain)

    await loader.insert(
        "oso.int_events__blockchain",
        [
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
