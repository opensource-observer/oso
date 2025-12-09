from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcoDeveloperContributionRanks(BaseModel):
    """Seed model for opendevdata eco_developer_contribution_ranks"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    day: date | None = Column("DATE", description="day")
    points: int | None = Column("BIGINT", description="points")
    points_28d: int | None = Column("BIGINT", description="points 28d")
    points_56d: int | None = Column("BIGINT", description="points 56d")
    contribution_rank: str | None = Column("VARCHAR", description="contribution rank")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="eco_developer_contribution_ranks",
    base=EcoDeveloperContributionRanks,
    rows=[
        EcoDeveloperContributionRanks(
            ecosystem_id=5,
            canonical_developer_id=859769,
            day=date.fromisoformat("2020-04-29"),
            points=10,
            points_28d=10,
            points_56d=10,
            contribution_rank="full_time",
        ),
        EcoDeveloperContributionRanks(
            ecosystem_id=12096,
            canonical_developer_id=204871,
            day=date.fromisoformat("2021-10-10"),
            points=10,
            points_28d=4,
            points_56d=10,
            contribution_rank="full_time",
        ),
        EcoDeveloperContributionRanks(
            ecosystem_id=5280,
            canonical_developer_id=142613,
            day=date.fromisoformat("2017-03-13"),
            points=10,
            points_28d=4,
            points_56d=4,
            contribution_rank="full_time",
        ),
        EcoDeveloperContributionRanks(
            ecosystem_id=391,
            canonical_developer_id=82021,
            day=date.fromisoformat("2023-07-13"),
            points=10,
            points_28d=0,
            points_56d=4,
            contribution_rank="full_time",
        ),
        EcoDeveloperContributionRanks(
            ecosystem_id=16113,
            canonical_developer_id=23063,
            day=date.fromisoformat("2019-11-13"),
            points=4,
            points_28d=4,
            points_56d=10,
            contribution_rank="full_time",
        ),
    ],
)
