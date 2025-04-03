from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Sbom(BaseModel):
    artifact_namespace: str | None = Column("VARCHAR")
    artifact_name: str | None = Column("VARCHAR")
    artifact_source: str | None = Column("VARCHAR")
    package: str | None = Column("VARCHAR")
    package_source: str | None = Column("VARCHAR")
    package_version: str | None = Column("VARCHAR")
    snapshot_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    dlt_load_id: str = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="ossd",
    table="sbom",
    base=Sbom,
    rows=[
        Sbom(
            artifact_namespace="namespace1",
            artifact_name="artifact1",
            artifact_source="source1",
            package="package1",
            package_source="source1",
            package_version="1.0.0",
            snapshot_at=datetime.now(),
            dlt_load_id="load1",
            dlt_id="id1",
        ),
        Sbom(
            artifact_namespace="namespace2",
            artifact_name="artifact2",
            artifact_source="source2",
            package="package2",
            package_source="source2",
            package_version="2.0.0",
            snapshot_at=datetime.now(),
            dlt_load_id="load2",
            dlt_id="id2",
        ),
    ],
)
