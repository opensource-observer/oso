from datetime import datetime

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class Verifications(BaseModel):
    fid: int = Column("BIGINT")
    address: str = Column("VARCHAR")
    timestamp: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    deleted_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")


async def seed(loader: DestinationLoader):
    await loader.create_table("farcaster.verifications", Verifications)

    await loader.insert(
        "farcaster.verifications",
        [
            Verifications(
                fid=1, address="0x123", timestamp=datetime.now(), deleted_at=None
            ),
            Verifications(
                fid=2, address="0x456", timestamp=datetime.now(), deleted_at=None
            ),
        ],
    )
