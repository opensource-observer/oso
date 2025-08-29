from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class PackageVersionToProject(BaseModel):
    """Stores the mapping between package versions and projects"""

    SnapshotAt: datetime | None = Column(
        "TIMESTAMP", description="The timestamp of the snapshot"
    )
    System: str | None = Column(
        "VARCHAR",
        description="The dependency management system of the package-version.",
    )
    ProjectName: str | None = Column("VARCHAR", description="The name of the project.")
    ProjectType: str | None = Column("VARCHAR", description="The type of the project.")
    Name: str | None = Column("VARCHAR", description="The name of the package-version")
    Version: str | None = Column(
        "VARCHAR", description="The version of the package-version"
    )
    RelationType: str | None = Column(
        "VARCHAR",
        description="What the relationship between the project and the package version is.",
    )


seed = SeedConfig(
    catalog="bigquery_public_data",
    schema="deps_dev_v1",
    table="PackageVersionToProject",
    base=PackageVersionToProject,
    rows=[
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="CARGO",
            ProjectName="scrtlabs/cosmwasm",
            ProjectType="GITHUB",
            Name="secret-cosmwasm-crypto",
            Version="1.1.11",
            RelationType="SOURCE_REPO_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="GO",
            ProjectName="compass/compass",
            ProjectType="GITHUB",
            Name="github.com/compass/compass",
            Version="v0.6.9",
            RelationType="SOURCE_REPO_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="MAVEN",
            ProjectName="aspectran/aspectran",
            ProjectType="GITHUB",
            Name="com.aspectran:aspectran",
            Version="5.7.0",
            RelationType="ISSUE_TRACKER_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="MAVEN",
            ProjectName="eventoframework/evento-framework",
            ProjectType="GITHUB",
            Name="com.eventoframework:evento-common",
            Version="ev1.8.1",
            RelationType="SOURCE_REPO_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="NPM",
            ProjectName="pngwn/mdsvex",
            ProjectType="GITHUB",
            Name="mdsvex",
            Version="0.5.3",
            RelationType="ISSUE_TRACKER_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="NPM",
            ProjectName="rlthomasgames/kitsune",
            ProjectType="GITHUB",
            Name="kitsune-wrapper-library",
            Version="0.0.34",
            RelationType="SOURCE_REPO_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="NUGET",
            ProjectName="matheusneder/graceterm",
            ProjectType="GITHUB",
            Name="graceterm",
            Version="1.0.0-alpha-b0",
            RelationType="SOURCE_REPO_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="PYPI",
            ProjectName="home-assistant/core",
            ProjectType="GITHUB",
            Name="homeassistant",
            Version="2024.1.0b5",
            RelationType="ISSUE_TRACKER_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="PYPI",
            ProjectName="greytechno/gtci",
            ProjectType="GITHUB",
            Name="gtci",
            Version="1.0.6",
            RelationType="SOURCE_REPO_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="RUBYGEMS",
            ProjectName="fmmfonseca/work_queue",
            ProjectType="GITHUB",
            Name="work_queue",
            Version="2.5.1",
            RelationType="ISSUE_TRACKER_TYPE",
        ),
        PackageVersionToProject(
            SnapshotAt=datetime.now(),
            System="RUBYGEMS",
            ProjectName="jarmo/watirsplash",
            ProjectType="GITHUB",
            Name="watirsplash",
            Version="0.2.10",
            RelationType="SOURCE_REPO_TYPE",
        ),
    ],
)
