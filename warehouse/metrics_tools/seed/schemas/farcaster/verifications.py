from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Verifications(BaseModel):
    fid: int = Column("BIGINT")
    address: str = Column("VARCHAR")
    timestamp: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    deleted_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")


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
