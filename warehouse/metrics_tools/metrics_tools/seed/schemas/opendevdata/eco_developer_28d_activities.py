from datetime import date
from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class RepoIdElement(BaseModel):
    element: int


class RepoIdsList(BaseModel):
    list: List[RepoIdElement]


class EcoDeveloper28DActivities(BaseModel):
    """Seed model for opendevdata eco_developer_28d_activities"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    day: date | None = Column("DATE", description="day")
    repo_ids: Optional[RepoIdsList] = Column(
        "ROW(list ARRAY(ROW(element BIGINT)))", description="repo ids"
    )
    num_commits: int | None = Column("BIGINT", description="num commits")
    original_day: date | None = Column("DATE", description="original day")
    is_exclusive_28d: bool | None = Column("BOOLEAN", description="is exclusive 28d")
    l28_days: int | None = Column("BIGINT", description="l28 days")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="eco_developer_28d_activities",
    base=EcoDeveloper28DActivities,
    rows=[
        EcoDeveloper28DActivities(
            ecosystem_id=12896,
            canonical_developer_id=2755596,
            day=date.fromisoformat("2020-08-23"),
            repo_ids=RepoIdsList(list=[RepoIdElement(element=17060405)]),
            num_commits=42,
            original_day=date.fromisoformat("2020-07-27"),
            is_exclusive_28d=True,
            l28_days=12,
        ),
        EcoDeveloper28DActivities(
            ecosystem_id=12717,
            canonical_developer_id=394777,
            day=date.fromisoformat("2019-12-11"),
            repo_ids=RepoIdsList(list=[RepoIdElement(element=804941)]),
            num_commits=34,
            original_day=date.fromisoformat("2019-11-15"),
            is_exclusive_28d=True,
            l28_days=10,
        ),
        EcoDeveloper28DActivities(
            ecosystem_id=11554,
            canonical_developer_id=256316,
            day=date.fromisoformat("2025-04-18"),
            repo_ids=RepoIdsList(list=[RepoIdElement(element=10446786)]),
            num_commits=60,
            original_day=date.fromisoformat("2025-03-24"),
            is_exclusive_28d=False,
            l28_days=9,
        ),
        EcoDeveloper28DActivities(
            ecosystem_id=17118,
            canonical_developer_id=146270,
            day=date.fromisoformat("2022-10-13"),
            repo_ids=RepoIdsList(list=[RepoIdElement(element=464179)]),
            num_commits=120,
            original_day=date.fromisoformat("2022-09-19"),
            is_exclusive_28d=False,
            l28_days=10,
        ),
        EcoDeveloper28DActivities(
            ecosystem_id=9160,
            canonical_developer_id=146917,
            day=date.fromisoformat("2023-03-18"),
            repo_ids=RepoIdsList(list=[RepoIdElement(element=410772)]),
            num_commits=127,
            original_day=date.fromisoformat("2023-02-21"),
            is_exclusive_28d=True,
            l28_days=9,
        ),
    ],
)
