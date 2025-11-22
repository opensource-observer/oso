from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcoDeveloperActivities(BaseModel):
    """Seed model for opendevdata eco_developer_activities"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    day: date | None = Column("DATE", description="day")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    repo_ids: str | None = Column("TEXT", description="repo ids")
    num_commits: int | None = Column("BIGINT", description="num commits")
    is_exclusive: bool | None = Column("BOOLEAN", description="is exclusive")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="eco_developer_activities",
    base=EcoDeveloperActivities,
    rows=[
        EcoDeveloperActivities(
            ecosystem_id=1,
            day=date.fromisoformat("2023-02-02"),
            canonical_developer_id=146891,
            repo_ids="[697325]",
            num_commits=1,
            is_exclusive=False,
        ),
        EcoDeveloperActivities(
            ecosystem_id=1,
            day=date.fromisoformat("2023-06-12"),
            canonical_developer_id=90806,
            repo_ids="[879066]",
            num_commits=1,
            is_exclusive=True,
        ),
        EcoDeveloperActivities(
            ecosystem_id=1,
            day=date.fromisoformat("2023-08-30"),
            canonical_developer_id=51028,
            repo_ids="[859270]",
            num_commits=1,
            is_exclusive=True,
        ),
        EcoDeveloperActivities(
            ecosystem_id=1,
            day=date.fromisoformat("2021-06-18"),
            canonical_developer_id=43539,
            repo_ids="[320765]",
            num_commits=1,
            is_exclusive=True,
        ),
        EcoDeveloperActivities(
            ecosystem_id=1,
            day=date.fromisoformat("2013-05-02"),
            canonical_developer_id=29755,
            repo_ids="[57448]",
            num_commits=1,
            is_exclusive=True,
        ),
    ],
)
