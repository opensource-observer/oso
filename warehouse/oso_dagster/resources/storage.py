import typing as t
from contextlib import contextmanager

from dagster import ConfigurableResource
from google.cloud import storage
from metrics_tools.transfer.gcs import GCSTimeOrderedStorage
from metrics_tools.transfer.storage import TimeOrderedStorage
from pydantic import Field


class TimeOrderedStorageResource(ConfigurableResource):
    @contextmanager
    def get(self, prefix: str) -> t.Generator[TimeOrderedStorage, None]:
        raise NotImplementedError("Not implemented")


class GCSTimeOrderedStorageResource(TimeOrderedStorageResource):
    bucket_name: str = Field(
        description="The name of the GCS bucket to use for storage"
    )

    @contextmanager
    def get(self, prefix: str) -> t.Generator[TimeOrderedStorage, None]:
        client = storage.Client()
        yield GCSTimeOrderedStorage(
            client=client, bucket_name=self.bucket_name, prefix=prefix
        )
