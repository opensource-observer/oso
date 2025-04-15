from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Repositories(BaseModel):
    ingestion_time: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    id: int | None = Column("BIGINT")
    node_id: str | None = Column("VARCHAR")
    name_with_owner: str | None = Column("VARCHAR")
    url: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    is_fork: bool | None = Column("BOOLEAN")
    branch: str | None = Column("VARCHAR")
    fork_count: int | None = Column("BIGINT")
    star_count: int | None = Column("BIGINT")
    watcher_count: int | None = Column("BIGINT")
    license_spdx_id: str | None = Column("VARCHAR")
    license_name: str | None = Column("VARCHAR")
    language: str | None = Column("VARCHAR")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")
    owner: str | None = Column("VARCHAR")
    created_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")


seed = SeedConfig(
    catalog="bigquery",
    schema="ossd",
    table="repositories",
    base=Repositories,
    rows=[
        Repositories(
            ingestion_time=datetime.now() - timedelta(days=1),
            id=1,
            node_id="node1",
            name_with_owner="owner1/repo1",
            url="https://github.com/owner1/repo1",
            name="repo1",
            is_fork=False,
            branch="main",
            fork_count=10,
            star_count=100,
            watcher_count=50,
            license_spdx_id="MIT",
            license_name="MIT License",
            language="python",
            dlt_load_id="load1",
            dlt_id="id1",
            owner="owner1",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now(),
        ),
        Repositories(
            ingestion_time=datetime.now() - timedelta(days=1),
            id=2,
            node_id="node2",
            name_with_owner="owner2/repo2",
            url="https://github.com/owner2/repo2",
            name="repo2",
            is_fork=True,
            branch="main",
            fork_count=20,
            star_count=200,
            watcher_count=100,
            license_spdx_id="GPL-3.0",
            license_name="GNU General Public License v3.0",
            language="javaScript",
            dlt_load_id="load2",
            dlt_id="id2",
            owner="owner2",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now(),
        ),
    ],
)
