import typing as t
from contextlib import asynccontextmanager

from dagster import ConfigurableResource
from gcloud.aio import storage
from metrics_tools.transfer.gcs import GCSTimeOrderedStorage
from metrics_tools.transfer.storage import TimeOrderedStorage
from pydantic import Field


class TimeOrderedStorageResource(ConfigurableResource):
    @asynccontextmanager
    def get(self, prefix: str) -> t.AsyncIterator[TimeOrderedStorage]:
        raise NotImplementedError("Not implemented")


class GCSTimeOrderedStorageResource(TimeOrderedStorageResource):
    bucket_name: str = Field(
        description="The name of the GCS bucket to use for storage"
    )

    @asynccontextmanager
    async def get(self, prefix: str) -> t.AsyncIterator[TimeOrderedStorage]:
        async with storage.Storage() as client:
            yield GCSTimeOrderedStorage(
                client=client, bucket_name=self.bucket_name, prefix=prefix
            )
