from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from pydantic import BaseModel, Field


class Collections(BaseModel):
    version: int | None = Field(json_schema_extra={"sql": "BIGINT"})
    name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    display_name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    projects: list[str] = Field(json_schema_extra={"sql": "ARRAY(VARCHAR)"})
    description: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    sha: bytes | None = Field(json_schema_extra={"sql": "VARBINARY"})
    committed_time: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )


async def seed(loader: DestinationLoader):
    await loader.create_table("ossd.collections", Collections)

    await loader.insert(
        "ossd.collections",
        [
            Collections(
                version=1,
                name="collection1",
                display_name="Collection 1",
                projects=["project1", "project2"],
                description="Description 1",
                sha=None,
                committed_time=datetime.now(),
            ),
            Collections(
                version=2,
                name="collection2",
                display_name="Collection 2",
                projects=["project3", "project4"],
                description="Description 2",
                sha=None,
                committed_time=datetime.now(),
            ),
        ],
    )
