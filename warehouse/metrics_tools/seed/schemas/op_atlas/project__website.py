from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectWebsite(BaseModel):
    value: str | None = Column("VARCHAR")
    dlt_parent_id: str = Column("VARCHAR", column_name="_dlt_parent_id")
    dlt_list_idx: int = Column("BIGINT", column_name="_dlt_list_idx")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project__website",
    base=ProjectWebsite,
    rows=[
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
