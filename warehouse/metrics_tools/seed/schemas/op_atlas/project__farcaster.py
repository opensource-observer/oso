from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class ProjectFarcaster(BaseModel):
    value: str | None = Column("VARCHAR")
    dlt_parent_id: str = Column("VARCHAR", "_dlt_parent_id")
    dlt_list_idx: int = Column("BIGINT", "_dlt_list_idx")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


async def seed(loader: DestinationLoader):
    await loader.create_table("op_atlas.project__farcaster", ProjectFarcaster)

    await loader.insert(
        "op_atlas.project__farcaster",
        [
            ProjectFarcaster(
                value="farcaster1",
                dlt_parent_id="parent1",
                dlt_list_idx=1,
                dlt_id="dlt1",
            ),
            ProjectFarcaster(
                value="farcaster2",
                dlt_parent_id="parent2",
                dlt_list_idx=2,
                dlt_id="dlt2",
            ),
        ],
    )
