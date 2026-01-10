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
            value="https://soliditylang.org/",
            dlt_parent_id="vh0m30QNSQHp1g",
            dlt_list_idx=0,
            dlt_id="jFiXNVfTTX3l9A",
        ),
        ProjectWebsite(
            value="https://soliditylang.org/",
            dlt_parent_id="w7iRlKxZn25cdg",
            dlt_list_idx=0,
            dlt_id="CprxSHI8nPkNzg",
        ),
        ProjectWebsite(
            value="https://velodrome.finance",
            dlt_parent_id="yMTcvWZwiZs5LA",
            dlt_list_idx=0,
            dlt_id="xcT/vRFHUjHYbA",
        ),
        ProjectWebsite(
            value="https://www.erc4337.io/",
            dlt_parent_id="O9Iu+1cGb3F3Ng",
            dlt_list_idx=0,
            dlt_id="AUYyn4skKW5wWA",
        ),
    ],
)
