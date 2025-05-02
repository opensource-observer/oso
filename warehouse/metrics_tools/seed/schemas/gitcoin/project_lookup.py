
from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectLookup(BaseModel):
    group_id: str | None = Column("STRING")
    project_id: str | None = Column("STRING")
    source: str | None = Column("STRING")

seed = SeedConfig(
    catalog="bigquery",
    schema="gitcoin",
    table="project_lookup",
    base=ProjectLookup,
    rows=[
        ProjectLookup(
            group_id="0",
            project_id="7",
            source="cGrants",
        ),
        ProjectLookup(
            group_id="0",
            project_id="23",
            source="cGrants",
        ),
        ProjectLookup(
            group_id="1",
            project_id="9",
            source="cGrants",
        ),
        ProjectLookup(
            group_id="1",
            project_id="22",
            source="cGrants",
        ),
        ProjectLookup(
            group_id="10",
            project_id="0x68bf035f1ecb5914aede9bcae5512d0f3efa2c9f4cd7e3c7a69c7cb5836418b4",
            source="indexer",
        ),
        ProjectLookup(
            group_id="10",
            project_id="0xcc52492e46dbd2c54cdb936a81a470abfd16bf20f0733a8734a7da9c122cbf2d",
            source="indexer",
        ),
        ProjectLookup(
            group_id="10",
            project_id="0xcc52492e46dbd2c54cdb936a81a470abfd16bf20f0733a8734a7da9c122cbf2d",
            source="indexer",
        ),
        ProjectLookup(
            group_id="10",
            project_id="0x68bf035f1ecb5914aede9bcae5512d0f3efa2c9f4cd7e3c7a69c7cb5836418b4",
            source="indexer",
        ),
        ProjectLookup(
            group_id="10",
            project_id="0xcc52492e46dbd2c54cdb936a81a470abfd16bf20f0733a8734a7da9c122cbf2d",
            source="indexer",
        ),
        ProjectLookup(
            group_id="10",
            project_id="25",
            source="cGrants",
        ),
    ],
)
