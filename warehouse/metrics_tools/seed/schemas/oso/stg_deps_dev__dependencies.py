from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Dependency(BaseModel):
    System: str | None = Column("VARCHAR")
    Name: str | None = Column("VARCHAR")
    Version: str | None = Column("VARCHAR")


class StgDepsDevDependencies(BaseModel):
    snapshotat: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    system: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    version: str | None = Column("VARCHAR")
    dependency: Dependency | None = Column("ROW(?)")
    minimumdepth: int | None = Column("BIGINT")


seed = SeedConfig(
    catalog="bigquery",
    schema="oso",
    table="stg_deps_dev__dependencies",
    base=StgDepsDevDependencies,
    rows=[
        StgDepsDevDependencies(
            snapshotat=datetime.now(),
            system="system1",
            name="name1",
            version="1.0",
            dependency=Dependency(System="systemA", Name="nameA", Version="1.0"),
            minimumdepth=1,
        ),
        StgDepsDevDependencies(
            snapshotat=datetime.now(),
            system="system2",
            name="name2",
            version="2.0",
            dependency=Dependency(System="systemB", Name="nameB", Version="2.0"),
            minimumdepth=2,
        ),
    ],
)
