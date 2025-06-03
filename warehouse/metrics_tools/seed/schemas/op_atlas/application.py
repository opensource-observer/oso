from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Application(BaseModel):
    id: str = Column("VARCHAR")
    status: str = Column("VARCHAR")
    attestation_id: str = Column("VARCHAR")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    round_id: str = Column("VARCHAR")
    project_id: str = Column("VARCHAR")
    category_id: str | None = Column("VARCHAR")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="application",
    base=Application,
    rows=[
        Application(
            id="1",
            status="active",
            attestation_id="att1",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            round_id="round1",
            project_id="proj1",
            category_id="cat1",
            dlt_load_id="load1",
            dlt_id="dlt1",
        ),
        Application(
            id="2",
            status="inactive",
            attestation_id="att2",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            round_id="round2",
            project_id="proj2",
            category_id="cat2",
            dlt_load_id="load2",
            dlt_id="dlt2",
        ),
    ],
)
