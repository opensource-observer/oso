import logging
import os
import typing as t
from datetime import datetime
from urllib.parse import urlparse

from gcloud.aio import storage
from metrics_service.types import ExportReference, ExportType
from metrics_tools.transfer.storage import TimeOrderedStorage, TimeOrderedStorageFile

logger = logging.getLogger(__name__)


class GCSTimeOrderedStorageFile(TimeOrderedStorageFile):
    def __init__(
        self,
        client: storage.Storage,
        bucket: storage.Bucket,
        blob_name: str,
        prefix: str,
    ):
        self.blob_name = blob_name
        self.client = client
        self.prefix = prefix
        self.bucket = bucket

    @property
    def stored_time(self):
        name = t.cast(str, self.blob_name)
        export_rel_path = os.path.relpath(name, self.prefix)
        path_parts = export_rel_path.split("/")
        time = datetime.strptime("/".join(path_parts[0:4]), "%Y/%m/%d/%H")
        return time

    @property
    def time_part(self):
        name = t.cast(str, self.blob_name)
        export_rel_path = os.path.relpath(name, self.prefix)
        path_parts = export_rel_path.split("/")
        return "/".join(path_parts[0:4])

    @property
    def uri(self) -> str:
        return f"gs://{self.bucket.name}/{self.full_path}"

    @property
    def full_path(self) -> str:
        return t.cast(str, self.blob_name)

    @property
    def rel_path(self) -> str:
        return os.path.relpath(
            self.full_path, os.path.join(self.prefix, self.time_part)
        )

    @property
    def name(self) -> str:
        return os.path.basename(self.full_path)

    async def delete(self):
        await self.client.delete(self.bucket.name, self.blob_name)
        # self.blob.delete(if_generation_match=self.blob.generation)


class GCSTimeOrderedStorage(TimeOrderedStorage):
    """We use gcs as a substrate to transfer data between different systems. To
    keep that data organized we store it in a time ordered fashion. We could
    also use creation time but this was more explicit for both organizing the
    files and also scales to any file based storage system"""

    def __init__(self, *, client: storage.Storage, bucket_name: str, prefix: str):
        self.client = client
        self.bucket_name = bucket_name
        self.prefix = prefix

    def generate_path(self, stored_time: datetime, *joins: str):
        return os.path.join(
            f"gs://{self.bucket_name}/",
            self.prefix,
            stored_time.strftime("%Y/%m/%d/%H"),
            *joins,
        )

    def bucket(self, name):
        return storage.Bucket(self.client, name)

    async def iter_files(
        self,
        *,
        search_prefix: str = "",
        export_reference: t.Optional[ExportReference] = None,
        before: t.Optional[datetime] = None,
        after: t.Optional[datetime] = None,
    ) -> t.AsyncIterable[TimeOrderedStorageFile]:
        """Iterate through all the files in the bucket that are within the time
        range.

        Args:
            before (t.Optional[datetime], optional): Exclusive upper boundary. Defaults to None.
            after (t.Optional[datetime], optional): Inclusive lower boundary. Defaults to None.
            search_prefix (str, optional): The prefix to search for. Defaults to "".
            export_reference (t.Optional[ExportReference], optional): The export reference to search for. Defaults to None.

        Yields:
            t.Iterable[TimeOrderedStorageFile]: The files in the time range
        """
        bucket = self.bucket(self.bucket_name)

        if search_prefix and export_reference:
            raise ValueError("Cannot specify both search_prefix and export_reference")

        if search_prefix:
            search_prefix = os.path.join(self.prefix, search_prefix)
        elif export_reference:
            if export_reference.type != ExportType.GCS:
                raise ValueError("Can only search for GCS export references")
            gcs_path = export_reference.payload["gcs_path"]
            parsed_gcs_path = urlparse(gcs_path)
            # remove leading and trailing slashes otherwise the resulting blobs
            # will be empty
            search_prefix = parsed_gcs_path.path.strip("/")
        else:
            search_prefix = self.prefix
        logger.debug(f"Searching for blobs with prefix: {search_prefix}")

        blobs = await bucket.list_blobs(prefix=search_prefix)

        # Parse the insertion time
        for blob_name in blobs:
            f = GCSTimeOrderedStorageFile(self.client, bucket, blob_name, self.prefix)
            try:
                stored_time = f.stored_time
            except ValueError:
                logger.warning(
                    f"Could not parse time from {f.full_path}. probably not part of the time ordered storage"
                )
                continue

            if before:
                if stored_time > before:
                    continue
            if after:
                if stored_time <= after:
                    continue
            yield f
