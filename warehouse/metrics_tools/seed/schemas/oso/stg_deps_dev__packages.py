from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class StgDepsDevPackages(BaseModel):
    snapshotat: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    system: str | None = Column("VARCHAR")
    projectname: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    version: str | None = Column("VARCHAR")


async def seed(loader: DestinationLoader):
    await loader.create_table("oso.stg_deps_dev__packages", StgDepsDevPackages)

    await loader.insert(
        "oso.stg_deps_dev__packages",
        [
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
