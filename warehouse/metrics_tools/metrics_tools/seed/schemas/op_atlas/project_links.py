from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectLinks(BaseModel):
    id: str = Column("VARCHAR")
    url: str = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    description: str | None = Column("VARCHAR")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    project_id: str = Column("VARCHAR")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project_links",
    base=ProjectLinks,
    rows=[
        ProjectLinks(
            id="ba71300f-d058-4250-818e-f96b45d09462",
            url="https://soliditylang.org/",
            name="Website",
            description="The Solidity website with our blog and official documentation.",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8",
            dlt_load_id="1739198592.7361903",
            dlt_id="oAiy0CDTtKnKEQ",
        ),
        ProjectLinks(
            id="a7f7c8b3-b13b-4f82-b73f-853f2c93b078",
            url="https://forum.soliditylang.org/",
            name="Solidity Forum",
            description="The forum is a place for our user community to discuss topics related to the Solidity language design.",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8",
            dlt_load_id="1739198592.7361903",
            dlt_id="t/MJ0xsFcZ8uKg",
        ),
        ProjectLinks(
            id="89ad2d3c-ff46-4f13-b1cb-a6cde7da6d82",
            url="https://www.bundlebear.com/overview/all",
            name="Dashboard showing adoption",
            description="",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            dlt_load_id="1739198592.7361903",
            dlt_id="DbGOt4DBhS+xnQ",
        ),
    ],
)
