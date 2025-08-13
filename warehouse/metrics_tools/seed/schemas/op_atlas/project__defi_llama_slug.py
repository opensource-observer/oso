from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectDefiLlamaSlug(BaseModel):
    value: str | None = Column("VARCHAR")
    dlt_parent_id: str = Column("VARCHAR", column_name="_dlt_parent_id")
    dlt_list_idx: int = Column("BIGINT", column_name="_dlt_list_idx")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project__defi_llama_slug",
    base=ProjectDefiLlamaSlug,
    rows=[
        ProjectDefiLlamaSlug(
            value="velodrome-v2", 
            dlt_parent_id="yMTcvWZwiZs5LA", 
            dlt_list_idx=0, 
            dlt_id="8QToGGq1GAv9vw"
        ),
        ProjectDefiLlamaSlug(
            value="velodrome-v1", 
            dlt_parent_id="yMTcvWZwiZs5LA", 
            dlt_list_idx=0, 
            dlt_id="zWQDRjRUnCoBQg"
        ),
    ],
)
