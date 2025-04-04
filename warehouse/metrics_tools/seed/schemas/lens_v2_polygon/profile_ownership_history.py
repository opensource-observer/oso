from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class DatastreamMetadata(BaseModel):
    uuid: str | None = Column("VARCHAR")
    source_timestamp: int | None = Column("BIGINT")


class ProfileOwnershipHistory(BaseModel):
    history_id: int | None = Column("BIGINT")
    profile_id: str | None = Column("VARCHAR")
    owned_by: str | None = Column("VARCHAR")
    tx_hash: str | None = Column("VARCHAR")
    block_hash: str | None = Column("VARCHAR")
    block_number: int | None = Column("BIGINT")
    log_index: int | None = Column("BIGINT")
    tx_index: int | None = Column("BIGINT")
    block_timestamp: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    datastream_metadata: DatastreamMetadata | None = Column("ROW(?)")


seed = SeedConfig(
    catalog="bigquery",
    schema="lens_v2_polygon",
    table="profile_ownership_history",
    base=ProfileOwnershipHistory,
    rows=[
        ProfileOwnershipHistory(
            history_id=1,
            profile_id="profile_1",
            owned_by="owner_1",
            tx_hash="tx_hash_1",
            block_hash="block_hash_1",
            block_number=1001,
            log_index=1,
            tx_index=1,
            block_timestamp=datetime.now() - timedelta(days=2),
            datastream_metadata=DatastreamMetadata(
                uuid="uuid_1", source_timestamp=1234567890
            ),
        ),
        ProfileOwnershipHistory(
            history_id=2,
            profile_id="profile_2",
            owned_by="owner_2",
            tx_hash="tx_hash_2",
            block_hash="block_hash_2",
            block_number=1002,
            log_index=2,
            tx_index=2,
            block_timestamp=datetime.now() - timedelta(days=1),
            datastream_metadata=DatastreamMetadata(
                uuid="uuid_2", source_timestamp=1234567891
            ),
        ),
    ],
)
