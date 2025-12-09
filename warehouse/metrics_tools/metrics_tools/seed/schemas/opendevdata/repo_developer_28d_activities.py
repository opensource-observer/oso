from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class RepoDeveloper28DActivities(BaseModel):
    """Seed model for opendevdata repo_developer_28d_activities"""

    repo_id: int | None = Column("BIGINT", description="repo id")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    day: date | None = Column("DATE", description="day")
    num_commits: int | None = Column("BIGINT", description="num commits")
    original_day: date | None = Column("DATE", description="original day")
    l28_days: int | None = Column("BIGINT", description="l28 days")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="repo_developer_28d_activities",
    base=RepoDeveloper28DActivities,
    rows=[
        RepoDeveloper28DActivities(
            repo_id=2159100,
            canonical_developer_id=425697,
            day=date.fromisoformat("2013-01-01"),
            num_commits=6,
            original_day=date.fromisoformat("2012-12-05"),
            l28_days=3,
        ),
        RepoDeveloper28DActivities(
            repo_id=1967851,
            canonical_developer_id=478688,
            day=date.fromisoformat("2013-01-01"),
            num_commits=1,
            original_day=date.fromisoformat("2012-12-06"),
            l28_days=1,
        ),
        RepoDeveloper28DActivities(
            repo_id=2159207,
            canonical_developer_id=55867,
            day=date.fromisoformat("2013-01-02"),
            num_commits=37,
            original_day=date.fromisoformat("2012-12-06"),
            l28_days=10,
        ),
        RepoDeveloper28DActivities(
            repo_id=1751281,
            canonical_developer_id=68105,
            day=date.fromisoformat("2013-01-01"),
            num_commits=14,
            original_day=date.fromisoformat("2012-12-06"),
            l28_days=5,
        ),
        RepoDeveloper28DActivities(
            repo_id=57874,
            canonical_developer_id=319850,
            day=date.fromisoformat("2013-01-01"),
            num_commits=1,
            original_day=date.fromisoformat("2012-12-05"),
            l28_days=1,
        ),
    ],
)
