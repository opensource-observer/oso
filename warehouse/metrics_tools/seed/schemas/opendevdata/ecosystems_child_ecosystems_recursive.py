from datetime import date, datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcosystemsChildEcosystemsRecursive(BaseModel):
    """Seed model for opendevdata ecosystems_child_ecosystems_recursive"""

    parent_id: int | None = Column("BIGINT", description="parent id")
    child_id: int | None = Column("BIGINT", description="child id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    ecosystem_ecosystem_paths: str | None = Column(
        "TEXT", description="ecosystem ecosystem paths"
    )
    ecosystem_chain_ecosystem_paths: str | None = Column(
        "TEXT", description="ecosystem chain ecosystem paths"
    )
    connection_dates: str | None = Column("TEXT", description="connection dates")
    connected_at: date | None = Column("DATE", description="connected at")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems_child_ecosystems_recursive",
    base=EcosystemsChildEcosystemsRecursive,
    rows=[
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=86,
            created_at=datetime.fromisoformat("2024-10-24 15:40:11"),
            ecosystem_ecosystem_paths="[12, 9503, 11554, 9455, 2, 7089, 86]",
            ecosystem_chain_ecosystem_paths="[2, 7089]",
            connection_dates='["2013-12-26", "2013-12-26", "2022-12-01", "2022-12-01", "2022-12-01", "2020-03-22", "2015-07-30", "2015-07-30", "2021-01-16", "2021-01-16", "2021-01-16", "2018-04-18"]',
            connected_at=date.fromisoformat("2022-12-01"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=83,
            created_at=datetime.fromisoformat("2024-11-09 00:00:17"),
            ecosystem_ecosystem_paths="[12, 9503, 11554, 9455, 2, 7089, 83]",
            ecosystem_chain_ecosystem_paths="[2, 7089]",
            connection_dates='["2013-12-26", "2013-12-26", "2022-12-01", "2022-12-01", "2022-12-01", "2020-03-22", "2015-07-30", "2015-07-30", "2021-01-16", "2021-01-16", "2021-01-16", "2018-04-30"]',
            connected_at=date.fromisoformat("2022-12-01"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=83,
            created_at=datetime.fromisoformat("2024-11-09 00:00:17"),
            ecosystem_ecosystem_paths="[12, 9503, 11435, 9455, 2, 7089, 83]",
            ecosystem_chain_ecosystem_paths="[2, 7089]",
            connection_dates='["2013-12-26", "2013-12-26", "2018-09-21", "2018-09-21", "2020-03-22", "2020-03-22", "2015-07-30", "2015-07-30", "2021-01-16", "2021-01-16", "2021-01-16", "2018-04-30"]',
            connected_at=date.fromisoformat("2021-01-16"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=78,
            created_at=datetime.fromisoformat("2024-10-24 15:40:11"),
            ecosystem_ecosystem_paths="[12, 9503, 11554, 9455, 2, 9562, 78]",
            ecosystem_chain_ecosystem_paths="[2, 9562, 78]",
            connection_dates='["2013-12-26", "2013-12-26", "2022-12-01", "2022-12-01", "2022-12-01", "2020-03-22", "2015-07-30", "2015-07-30", "2020-09-11", "2020-09-11", "2020-09-11", "2018-09-08"]',
            connected_at=date.fromisoformat("2022-12-01"),
        ),
        EcosystemsChildEcosystemsRecursive(
            parent_id=12,
            child_id=78,
            created_at=datetime.fromisoformat("2024-10-24 15:40:11"),
            ecosystem_ecosystem_paths="[12, 9503, 11435, 9455, 2, 9562, 78]",
            ecosystem_chain_ecosystem_paths="[2, 9562, 78]",
            connection_dates='["2013-12-26", "2013-12-26", "2018-09-21", "2018-09-21", "2020-03-22", "2020-03-22", "2015-07-30", "2015-07-30", "2020-09-11", "2020-09-11", "2020-09-11", "2018-09-08"]',
            connected_at=date.fromisoformat("2020-09-11"),
        ),
    ],
)
