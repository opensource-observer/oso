from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class L2beatActivity(BaseModel):
    """Stores L2beat activity data for various blockchain projects"""

    project_slug: str | None = Column(
        "VARCHAR", description="The slug identifier for the blockchain project"
    )
    timestamp: int | None = Column(
        "INTEGER", description="Unix timestamp of the data point"
    )
    count: int | None = Column("BIGINT", description="Number of transactions")
    uops_count: int | None = Column("BIGINT", description="Number of user operations")


seed = SeedConfig(
    catalog="bigquery",
    schema="l2beat",
    table="activity",
    base=L2beatActivity,
    rows=[
        L2beatActivity(
            project_slug="mantle",
            timestamp=int(datetime.now().timestamp()),
            count=192429,
            uops_count=193054,
        ),
        L2beatActivity(
            project_slug="linea",
            timestamp=int(datetime.now().timestamp()),
            count=152585,
            uops_count=152644,
        ),
        L2beatActivity(
            project_slug="base",
            timestamp=int(datetime.now().timestamp()),
            count=9718445,
            uops_count=9868176,
        ),
        L2beatActivity(
            project_slug="arbitrum",
            timestamp=int(datetime.now().timestamp()),
            count=2170249,
            uops_count=2194371,
        ),
        L2beatActivity(
            project_slug="polygon-pos",
            timestamp=int(datetime.now().timestamp()),
            count=3986125,
            uops_count=4175707,
        ),
    ],
)
