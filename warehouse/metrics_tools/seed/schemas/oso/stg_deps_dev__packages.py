from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from pydantic import BaseModel, Field

# CREATE TABLE IF NOT EXISTS bigquery.oso.stg_deps_dev__packages (
#    snapshotat timestamp(6) with time zone,
#    system varchar,
#    projectname varchar,
#    name varchar,
#    version varchar
# );


class StgDepsDevPackages(BaseModel):
    snapshotat: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )
    system: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    projectname: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    version: str | None = Field(json_schema_extra={"sql": "VARCHAR"})


async def seed(loader: DestinationLoader):
    await loader.create_table("oso.stg_deps_dev__packages", StgDepsDevPackages)

    await loader.insert(
        "oso.stg_deps_dev__packages",
        [
            StgDepsDevPackages(
                snapshotat=datetime.now(),
                system="system1",
                projectname="owner/repo/project1",
                name="name1",
                version="1.0",
            ),
            StgDepsDevPackages(
                snapshotat=datetime.now(),
                system="system2",
                projectname="owner/repo/project2",
                name="name2",
                version="2.0",
            ),
        ],
    )
