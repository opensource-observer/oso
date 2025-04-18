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
            id="1",
            url="http://link1.com",
            name="Link One",
            description="Description One",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="proj1",
            dlt_load_id="load1",
            dlt_id="dlt1",
        ),
        ProjectLinks(
            id="2",
            url="http://link2.com",
            name="Link Two",
            description="Description Two",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="proj2",
            dlt_load_id="load2",
            dlt_id="dlt2",
        ),
    ],
)
