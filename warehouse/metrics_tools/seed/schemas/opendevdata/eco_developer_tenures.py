from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class EcoDeveloperTenures(BaseModel):
    """Seed model for opendevdata eco_developer_tenures"""

    ecosystem_id: int | None = Column("BIGINT", description="ecosystem id")
    canonical_developer_id: int | None = Column(
        "BIGINT", description="canonical developer id"
    )
    day: date | None = Column("DATE", description="day")
    tenure_days: int | None = Column("BIGINT", description="tenure days")
    category: int | None = Column("BIGINT", description="category")


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="eco_developer_tenures",
    base=EcoDeveloperTenures,
    rows=[
        EcoDeveloperTenures(
            ecosystem_id=12087,
            canonical_developer_id=327260,
            day=date.fromisoformat("2024-05-18"),
            tenure_days=25,
            category=0,
        ),
        EcoDeveloperTenures(
            ecosystem_id=17111,
            canonical_developer_id=302359,
            day=date.fromisoformat("2024-10-07"),
            tenure_days=209,
            category=0,
        ),
        EcoDeveloperTenures(
            ecosystem_id=11436,
            canonical_developer_id=292078,
            day=date.fromisoformat("2023-03-19"),
            tenure_days=46,
            category=0,
        ),
        EcoDeveloperTenures(
            ecosystem_id=11436,
            canonical_developer_id=269773,
            day=date.fromisoformat("2023-11-27"),
            tenure_days=164,
            category=0,
        ),
        EcoDeveloperTenures(
            ecosystem_id=16221,
            canonical_developer_id=267,
            day=date.fromisoformat("2025-05-09"),
            tenure_days=282,
            category=0,
        ),
    ],
)
