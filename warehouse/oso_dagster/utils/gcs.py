from google.cloud.storage import Client
from typing import List


def batch_delete_blobs(
    gcs_client: Client, bucket_name: str, blobs: List[str], batch_size: int
):
    bucket = gcs_client.bucket(bucket_name)

    batch: List[str] = []
    for blob in blobs:
        batch.append(blob)
        if len(batch) == batch_size:
            bucket.delete_blobs(blobs=batch)
    if len(batch) > 0:
        bucket.delete_blobs(blobs=batch)
