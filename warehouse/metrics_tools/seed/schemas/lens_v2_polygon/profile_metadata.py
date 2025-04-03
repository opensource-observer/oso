from datetime import datetime, timedelta
from typing import Any, Dict

from metrics_tools.seed.loader import DestinationLoader
from metrics_tools.seed.types import Column
from pydantic import BaseModel


class DatastreamMetadata(BaseModel):
    uuid: str | None = Column("VARCHAR")
    source_timestamp: int | None = Column("BIGINT")


class ProfileMetadata(BaseModel):
    id: int | None = Column("BIGINT")
    profile_id: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    bio: str | None = Column("VARCHAR")
    app: str | None = Column("VARCHAR")
    metadata_json: Dict[str, Any] | None = Column("JSON")
    metadata_version: str | None = Column("VARCHAR")
    metadata_uri: str | None = Column("VARCHAR")
    metadata_snapshot_location_url: str | None = Column("VARCHAR")
    profile_with_weights: str | None = Column("VARCHAR")
    profile_picture_snapshot_location_url: str | None = Column("VARCHAR")
    cover_picture_snapshot_location_url: str | None = Column("VARCHAR")
    transaction_executor: str | None = Column("VARCHAR")
    tx_hash: str | None = Column("VARCHAR")
    block_hash: str | None = Column("VARCHAR")
    block_number: int | None = Column("BIGINT")
    log_index: int | None = Column("BIGINT")
    tx_index: int | None = Column("BIGINT")
    block_timestamp: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    datastream_metadata: DatastreamMetadata | None = Column("ROW(?)")


async def seed(loader: DestinationLoader):
    await loader.create_table("lens_v2_polygon.profile_metadata", ProfileMetadata)

    await loader.insert(
        "lens_v2_polygon.profile_metadata",
        [
            ProfileMetadata(
                id=1,
                profile_id="profile_1",
                name="Alice",
                bio="Bio 1",
                app="App 1",
                metadata_json={
                    "$schema": "https://json-schemas.lens.dev/profile/2.0.0.json",
                    "lens": {
                        "id": "bde8f4d9-34a3-4d27-b98c-0b871f857dcd",
                        "name": "Alice",
                    },
                },
                metadata_version="v1",
                metadata_uri="uri_1",
                metadata_snapshot_location_url="snapshot_url_1",
                profile_with_weights="weights_1",
                profile_picture_snapshot_location_url="picture_url_1",
                cover_picture_snapshot_location_url="cover_url_1",
                transaction_executor="executor_1",
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
            ProfileMetadata(
                id=2,
                profile_id="profile_2",
                name="Bob",
                bio="Bio 2",
                app="App 2",
                metadata_json={
                    "$schema": "https://json-schemas.lens.dev/profile/2.0.0.json",
                    "lens": {
                        "id": "fcdd6027-b5de-4584-9ec5-557fc93ef7e6",
                        "name": "Bob",
                    },
                },
                metadata_version="v2",
                metadata_uri="uri_2",
                metadata_snapshot_location_url="snapshot_url_2",
                profile_with_weights="weights_2",
                profile_picture_snapshot_location_url="picture_url_2",
                cover_picture_snapshot_location_url="cover_url_2",
                transaction_executor="executor_2",
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
