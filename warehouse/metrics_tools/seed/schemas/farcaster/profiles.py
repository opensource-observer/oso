from datetime import datetime, timedelta
from typing import Any, Dict

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class Profiles(BaseModel):
    fid: int = Column("BIGINT")
    last_updated_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    data: Dict[str, Any] | None = Column("JSON")
    custody_address: str | None = Column("VARCHAR")


async def seed(loader: DestinationLoader):
    await loader.create_table("farcaster.profiles", Profiles)

    await loader.insert(
        "farcaster.profiles",
        [
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
