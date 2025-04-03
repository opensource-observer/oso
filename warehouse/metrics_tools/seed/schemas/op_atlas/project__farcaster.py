from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectFarcaster(BaseModel):
    value: str | None = Column("VARCHAR")
    dlt_parent_id: str = Column("VARCHAR", "_dlt_parent_id")
    dlt_list_idx: int = Column("BIGINT", "_dlt_list_idx")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project__farcaster",
    base=ProjectFarcaster,
    rows=[
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
