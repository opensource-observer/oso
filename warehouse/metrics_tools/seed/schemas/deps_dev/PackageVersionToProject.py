from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class PackageVersionToProject(BaseModel):
    """Stores the mapping between package versions and projects"""

    SnapshotAt: datetime | None = Column("TIMESTAMP", description="The timestamp of the snapshot")
    System: str | None = Column("VARCHAR", description="The dependency management system of the package-version.")
    ProjectName: str | None = Column("VARCHAR", description="The name of the project.")
    ProjectType: str | None = Column("VARCHAR", description="The type of the project.")
    Name: str | None = Column("VARCHAR", description="The name of the package-version" )
    Version: str | None = Column("VARCHAR", description="The version of the package-version")
    RelationType: str | None = Column("VARCHAR", description="What the relationship between the project and the package version is.")

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

