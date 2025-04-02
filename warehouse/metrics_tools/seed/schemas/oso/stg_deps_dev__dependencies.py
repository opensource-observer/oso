from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
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


async def seed(loader: DestinationLoader):
    await loader.create_table("oso.stg_deps_dev__dependencies", StgDepsDevDependencies)

    await loader.insert(
        "oso.stg_deps_dev__dependencies",
        [
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
