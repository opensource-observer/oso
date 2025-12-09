from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectFarcaster(BaseModel):
    value: str | None = Column("VARCHAR")
    dlt_parent_id: str = Column("VARCHAR", column_name="_dlt_parent_id")
    dlt_list_idx: int = Column("BIGINT", column_name="_dlt_list_idx")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project__farcaster",
    base=ProjectFarcaster,
    rows=[
        ProjectFarcaster(
            value="https://warpcast.com/velodrome",
            dlt_parent_id="yMTcvWZwiZs5LA",
            dlt_list_idx=0,
            dlt_id="UPtGQKfLn/99BQ",
        ),
        ProjectFarcaster(
            value="https://warpcast.com/soliditylang.eth",
            dlt_parent_id="vh0m30QNSQHp1g",
            dlt_list_idx=0,
            dlt_id="UYi1SKkAkAE48w",
        ),
        ProjectFarcaster(
            value="https://warpcast.com/soliditylang.eth",
            dlt_parent_id="w7iRlKxZn25cdg",
            dlt_list_idx=0,
            dlt_id="aI9RBZA78rcfPA",
        ),
    ],
)
