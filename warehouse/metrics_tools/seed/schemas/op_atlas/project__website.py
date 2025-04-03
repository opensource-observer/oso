from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class ProjectWebsite(BaseModel):
    value: str | None = Column("VARCHAR")
    dlt_parent_id: str = Column("VARCHAR", "_dlt_parent_id")
    dlt_list_idx: int = Column("BIGINT", "_dlt_list_idx")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


async def seed(loader: DestinationLoader):
    await loader.create_table("op_atlas.project__website", ProjectWebsite)

    await loader.insert(
        "op_atlas.project__website",
        [
            ProjectWebsite(
                value="http://website1.com",
                dlt_parent_id="parent1",
                dlt_list_idx=1,
                dlt_id="dlt1",
            ),
            ProjectWebsite(
                value="http://website2.com",
                dlt_parent_id="parent2",
                dlt_list_idx=2,
                dlt_id="dlt2",
            ),
        ],
    )
