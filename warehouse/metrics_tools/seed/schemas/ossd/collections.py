from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class Collections(BaseModel):
    version: int | None = Column("BIGINT")
    name: str | None = Column("VARCHAR")
    display_name: str | None = Column("VARCHAR")
    projects: list[str] = Column("ARRAY(VARCHAR)")
    description: str | None = Column("VARCHAR")
    sha: bytes | None = Column("VARBINARY")
    committed_time: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")


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
