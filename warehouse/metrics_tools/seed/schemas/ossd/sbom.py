from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from pydantic import BaseModel, Field


class Sbom(BaseModel):
    artifact_namespace: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    artifact_name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    artifact_source: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    package: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    package_source: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    package_version: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    snapshot_at: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )
    dlt_load_id: str = Field(alias="_dlt_load_id", json_schema_extra={"sql": "VARCHAR"})
    dlt_id: str = Field(alias="_dlt_id", json_schema_extra={"sql": "VARCHAR"})


async def seed(loader: DestinationLoader):
    await loader.create_table("ossd.sbom", Sbom)

    await loader.insert(
        "ossd.sbom",
        [
            Sbom(
                artifact_namespace="namespace1",
                artifact_name="artifact1",
                artifact_source="source1",
                package="package1",
                package_source="source1",
                package_version="1.0.0",
                snapshot_at=datetime.now(),
                _dlt_load_id="load1",
                _dlt_id="id1",
            ),
            Sbom(
                artifact_namespace="namespace2",
                artifact_name="artifact2",
                artifact_source="source2",
                package="package2",
                package_source="source2",
                package_version="2.0.0",
                snapshot_at=datetime.now(),
                _dlt_load_id="load2",
                _dlt_id="id2",
            ),
        ],
    )
