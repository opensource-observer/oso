from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class PackageVersionToProject(BaseModel):
    SnapshotAt: datetime | None = Column("TIMESTAMP")
    System: str | None = Column("VARCHAR")
    ProjectName: str | None = Column("VARCHAR")
    ProjectType: str | None = Column("VARCHAR")
    Name: str | None = Column("VARCHAR")
    Version: str | None = Column("VARCHAR")
    RelationType: str | None = Column("VARCHAR")

seed = SeedConfig(
    catalog="bigquery_public_data",
    schema="deps_dev_v1",
    table="PackageVersionToProject",
    base=PackageVersionToProject,
    rows=[
        PackageVersionToProject(
            SnapshotAt=datetime(2025, 3, 2),
            System="NPM",
            ProjectName="react",
            ProjectType="GITHUB",
            Name="react",
            Version="18.0.1",
            RelationType=None,
        ),
        PackageVersionToProject(
            SnapshotAt=datetime(2025, 3, 2),
            System="NPM",
            ProjectName="ethers",
            ProjectType="GITHUB",
            Name="ethers",
            Version="6.13.1",
            RelationType=None,
        ),
        PackageVersionToProject(
            SnapshotAt=datetime(2025, 3, 2),
            System="NPM",
            ProjectName="viem",
            ProjectType="GITHUB",
            Name="viem",
            Version="2.26.1",
            RelationType=None,
        ),
    ],
)

