from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Verifications(BaseModel):
    """Farcaster profile verifications"""

    fid: int = Column("BIGINT", description="The farcaster id")
    address: str = Column("VARCHAR", description="The address of the farcaster profile")
    timestamp: datetime = Column("TIMESTAMP(6) WITH TIME ZONE", description="The timestamp of the verification")
    deleted_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE", description="The timestamp of the verification's deletion")


seed = SeedConfig(
    catalog="bigquery",
    schema="farcaster",
    table="verifications",
    base=Verifications,
    rows=[
        Verifications(
            fid=1,
            address="0x123",
            timestamp=datetime.now() - timedelta(days=2),
            deleted_at=None,
        ),
        Verifications(
            fid=2,
            address="0x456",
            timestamp=datetime.now() - timedelta(days=1),
            deleted_at=None,
        ),
    ],
)
