from datetime import datetime, timedelta
from typing import Any, Dict

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Profiles(BaseModel):
    """Farcaster profile"""

    fid: int = Column("BIGINT", description="The farcaster id of the profile")
    last_updated_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE", description="The last updated time of the profile")
    data: Dict[str, Any] | None = Column("JSON", description="JSON farcaster data of the profile")
    custody_address: str | None = Column("VARCHAR", description="The custody address of the profile")


seed = SeedConfig(
    catalog="bigquery",
    schema="farcaster",
    table="profiles",
    base=Profiles,
    rows=[
        Profiles(
            fid=1,
            last_updated_at=datetime.now() - timedelta(days=2),
            data={"username": "Alice"},
            custody_address="0x123",
        ),
        Profiles(
            fid=2,
            last_updated_at=datetime.now() - timedelta(days=1),
            data={"username": "Bob"},
            custody_address="0x456",
        ),
    ],
)
