from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from pydantic import BaseModel, Field

# CREATE TABLE IF NOT EXISTS bigquery.oso.stg_deps_dev__dependencies (
#    snapshotat timestamp(6) with time zone,
#    system varchar,
#    name varchar,
#    version varchar,
#    dependency ROW(System varchar, Name varchar, Version varchar),
#    minimumdepth bigint
# );


class Dependency(BaseModel):
    System: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    Name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    Version: str | None = Field(json_schema_extra={"sql": "VARCHAR"})


class StgDepsDevDependencies(BaseModel):
    snapshotat: datetime | None = Field(
        json_schema_extra={"sql": "TIMESTAMP(6) WITH TIME ZONE"}
    )
    system: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    name: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    version: str | None = Field(json_schema_extra={"sql": "VARCHAR"})
    dependency: Dependency | None = Field(json_schema_extra={"sql": "ROW(?)"})
    minimumdepth: int | None = Field(json_schema_extra={"sql": "BIGINT"})


async def seed(loader: DestinationLoader):
    await loader.create_table("oso.stg_deps_dev__dependencies", StgDepsDevDependencies)

    await loader.insert(
        "oso.stg_deps_dev__dependencies",
        [
            StgDepsDevDependencies(
                snapshotat=datetime.now(),
                system="system1",
                name="name1",
                version="1.0",
                dependency=Dependency(System="systemA", Name="nameA", Version="1.0"),
                minimumdepth=1,
            ),
            StgDepsDevDependencies(
                snapshotat=datetime.now(),
                system="system2",
                name="name2",
                version="2.0",
                dependency=Dependency(System="systemB", Name="nameB", Version="2.0"),
                minimumdepth=2,
            ),
        ],
    )
