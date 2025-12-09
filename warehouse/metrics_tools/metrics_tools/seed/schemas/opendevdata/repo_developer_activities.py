from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class RepoDeveloperActivities(BaseModel):
    """Seed model for opendevdata repo_developer_activities"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    repo_id: int | None = Column("BIGINT", description="repo id")
    day: date | None = Column("DATE", description="day")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    num_commits: int | None = Column("BIGINT", description="num commits")
    is_explicit: bool | None = Column("BOOLEAN", description="is explicit")
    is_chain: int | None = Column("BIGINT", description="is chain")
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
    table="repo_developer_activities",
    base=RepoDeveloperActivities,
    rows=[
        RepoDeveloperActivities(
            ecosystem_id=1,
            repo_id=18075490,
            day=date.fromisoformat("2025-10-19"),
            canonical_developer_id=2596146,
            num_commits=1,
            is_explicit=False,
            is_chain=1,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        RepoDeveloperActivities(
            ecosystem_id=1,
            repo_id=959972,
            day=date.fromisoformat("2024-12-21"),
            canonical_developer_id=84055,
            num_commits=1,
            is_explicit=True,
            is_chain=1,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        RepoDeveloperActivities(
            ecosystem_id=1,
            repo_id=367422,
            day=date.fromisoformat("2023-02-07"),
            canonical_developer_id=209091,
            num_commits=1,
            is_explicit=False,
            is_chain=1,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        RepoDeveloperActivities(
            ecosystem_id=1,
            repo_id=8709,
            day=date.fromisoformat("2021-09-13"),
            canonical_developer_id=33357,
            num_commits=1,
            is_explicit=True,
            is_chain=1,
            is_direct_exclusive=False,
            is_indirect_exclusive=False,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
        RepoDeveloperActivities(
            ecosystem_id=1,
            repo_id=6595,
            day=date.fromisoformat("2021-06-28"),
            canonical_developer_id=31283,
            num_commits=1,
            is_explicit=False,
            is_chain=1,
            is_direct_exclusive=False,
            is_indirect_exclusive=True,
            exclusive_at_connection=True,
            exclusive_till=None,
        ),
    ],
)
