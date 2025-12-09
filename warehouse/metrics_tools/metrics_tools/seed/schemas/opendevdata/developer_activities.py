from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class DeveloperActivities(BaseModel):
    """Seed model for opendevdata developer_activities"""

    repo_id: int | None = Column("BIGINT", description="repo id")
    day: date | None = Column("DATE", description="day")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    num_commits: int | None = Column("BIGINT", description="num commits")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="developer_activities",
    base=DeveloperActivities,
    rows=[
        DeveloperActivities(
            repo_id=2341846,
            day=date.fromisoformat("2008-01-03"),
            canonical_developer_id=430058,
            num_commits=1,
        ),
        DeveloperActivities(
            repo_id=881141,
            day=date.fromisoformat("2008-01-01"),
            canonical_developer_id=1094693,
            num_commits=1,
        ),
        DeveloperActivities(
            repo_id=260378,
            day=date.fromisoformat("2008-01-01"),
            canonical_developer_id=420498,
            num_commits=1,
        ),
        DeveloperActivities(
            repo_id=429458,
            day=date.fromisoformat("2008-01-03"),
            canonical_developer_id=16973,
            num_commits=1,
        ),
        DeveloperActivities(
            repo_id=60536,
            day=date.fromisoformat("2008-01-02"),
            canonical_developer_id=139121,
            num_commits=1,
        ),
    ],
)
