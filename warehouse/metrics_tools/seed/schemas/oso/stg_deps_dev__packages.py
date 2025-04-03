from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class StgDepsDevPackages(BaseModel):
    snapshotat: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    system: str | None = Column("VARCHAR")
    projectname: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    version: str | None = Column("VARCHAR")


seed = SeedConfig(
    catalog="bigquery",
    schema="oso",
    table="stg_deps_dev__packages",
    base=StgDepsDevPackages,
    rows=[
        StgDepsDevPackages(
            snapshotat=datetime.now(),
            system="system1",
            projectname="owner/repo/project1",
            name="name1",
            version="1.0",
        ),
        StgDepsDevPackages(
            snapshotat=datetime.now(),
            system="system2",
            projectname="owner/repo/project2",
            name="name2",
            version="2.0",
        ),
    ],
)
