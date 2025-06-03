from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectRepository(BaseModel):
    id: str = Column("VARCHAR")
    type: str = Column("VARCHAR")
    url: str = Column("VARCHAR")
    verified: bool = Column("BOOLEAN")
    open_source: bool = Column("BOOLEAN")
    contains_contracts: bool = Column("BOOLEAN")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    project_id: str = Column("VARCHAR")
    description: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    crate: bool = Column("BOOLEAN")
    npm_package: bool = Column("BOOLEAN")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="project_repository",
    base=ProjectRepository,
    rows=[
        ProjectRepository(
            id="1",
            type="github",
            url="http://repo1.com",
            verified=True,
            open_source=True,
            contains_contracts=True,
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            project_id="proj1",
            description="Description One",
            name="Repo One",
            crate=True,
            npm_package=True,
            dlt_load_id="load1",
            dlt_id="dlt1",
        ),
        ProjectRepository(
            id="2",
            type="gitlab",
            url="http://repo2.com",
            verified=False,
            open_source=False,
            contains_contracts=False,
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            project_id="proj2",
            description="Description Two",
            name="Repo Two",
            crate=False,
            npm_package=False,
            dlt_load_id="load2",
            dlt_id="dlt2",
        ),
    ],
)
