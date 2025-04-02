from datetime import datetime, timedelta

from metrics_tools.seed.loader import DestinationLoader
from pydantic import BaseModel, Field


class Repositories(BaseModel):
    ingestion_time: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )
    id: int | None = Field(json_schema_extra={"sql": "BIGINT"})
    node_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    name_with_owner: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    url: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    is_fork: bool | None = Field(json_schema_extra={"sql": "BOOLEAN"})
    branch: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    fork_count: int | None = Field(json_schema_extra={"sql": "BIGINT"})
    star_count: int | None = Field(json_schema_extra={"sql": "BIGINT"})
    watcher_count: int | None = Field(json_schema_extra={"sql": "BIGINT"})
    license_spdx_id: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    license_name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    language: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    dlt_load_id: str = Field(alias="_dlt_load_id", json_schema_extra={"sql": "VARCHAR"})
    dlt_id: str = Field(alias="_dlt_id", json_schema_extra={"sql": "VARCHAR"})
    owner: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    created_at: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )
    updated_at: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )


async def seed(loader: DestinationLoader):
    await loader.create_table("ossd.repositories", Repositories)

    await loader.insert(
        "ossd.repositories",
        [
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
                _dlt_load_id="load1",
                _dlt_id="id1",
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
                _dlt_load_id="load2",
                _dlt_id="id2",
                owner="owner2",
                created_at=datetime.now() - timedelta(days=1),
                updated_at=datetime.now(),
            ),
        ],
    )
