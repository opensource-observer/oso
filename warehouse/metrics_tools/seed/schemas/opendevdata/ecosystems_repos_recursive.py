from datetime import date, datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcosystemsReposRecursive(BaseModel):
    """Seed model for opendevdata ecosystems_repos_recursive"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    repo_id: int | None = Column("BIGINT", description="repo id")
    created_at: datetime | None = Column("TIMESTAMP", description="created at")
    connected_at: date | None = Column("DATE", description="connected at")
    path: str | None = Column("TEXT", description="path")
    distance: int | None = Column("BIGINT", description="distance")
    is_explicit: bool | None = Column("BOOLEAN", description="is explicit")
    is_direct_exclusive: bool | None = Column(
        "BOOLEAN", description="is direct exclusive"
    )
    is_indirect_exclusive: bool | None = Column(
        "BOOLEAN", description="is indirect exclusive"
    )
    exclusive_at_connection: bool | None = Column(
        "BOOLEAN", description="exclusive at connection"
    )
    exclusive_till: date | None = Column("DATE", description="exclusive till")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="ecosystems_repos_recursive",
    base=EcosystemsReposRecursive,
    rows=[
        EcosystemsReposRecursive(
            ecosystem_id=17130,
            repo_id=1,
            created_at=datetime.fromisoformat("2019-05-24 21:03:16"),
            connected_at=date.fromisoformat("2017-08-01"),
            path="[17130, 3]",
            distance=2,
            is_explicit=False,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        EcosystemsReposRecursive(
            ecosystem_id=13887,
            repo_id=3,
            created_at=datetime.fromisoformat("2019-05-24 21:03:16"),
            connected_at=date.fromisoformat("2017-08-01"),
            path="[13887, 3]",
            distance=2,
            is_explicit=False,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        EcosystemsReposRecursive(
            ecosystem_id=13845,
            repo_id=2,
            created_at=datetime.fromisoformat("2019-05-24 21:03:16"),
            connected_at=date.fromisoformat("2017-08-01"),
            path="[13845, 13483, 3]",
            distance=3,
            is_explicit=False,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        EcosystemsReposRecursive(
            ecosystem_id=7163,
            repo_id=1,
            created_at=datetime.fromisoformat("2019-05-24 21:03:16"),
            connected_at=date.fromisoformat("2017-08-01"),
            path="[7163, 3]",
            distance=2,
            is_explicit=False,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        EcosystemsReposRecursive(
            ecosystem_id=7161,
            repo_id=3,
            created_at=datetime.fromisoformat("2019-05-24 21:03:16"),
            connected_at=date.fromisoformat("2017-08-01"),
            path="[7161, 3]",
            distance=2,
            is_explicit=False,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
    ],
)
