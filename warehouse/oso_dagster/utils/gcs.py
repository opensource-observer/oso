from google.cloud.storage import Client
from typing import List
from .errors import MalformedUrl

def gcs_to_http_url(gcs_path: str) -> str:
    """
    Converts a `gcs://` url to a `https://storage.googleapis.com/` url

    Parameters
    ----------
    gcs_path: str
        URL prefixed with gcs://
    
    Returns
    -------
    str
        HTTPS URL to the GCS object
    """
    if not gcs_path.startswith("gs://"):
        raise MalformedUrl(f"Expected gs:// prefix in {gcs_path}")
    return gcs_path.replace("gs://", "https://storage.googleapis.com/")

def batch_delete_blobs(
    gcs_client: Client, bucket_name: str, blobs: List[str], batch_size: int
):
    """
    Batch delete blobs

    Parameters
    ----------
    gcs_client: Client
        The Google Cloud Storage client
    bucket_name: str
        GCS bucket name
    blobs: List[str]
        List of GCS blobs to delete
    batch_size: int
        Number of blobs to delete at the same time
    """
    bucket = gcs_client.bucket(bucket_name)

    batch: List[str] = []
    for blob in blobs:
        batch.append(blob)
        if len(batch) == batch_size:
            # TODO: is this a bug? Should we reset the batch?
            bucket.delete_blobs(blobs=batch)
    if len(batch) > 0:
        bucket.delete_blobs(blobs=batch)

def batch_delete_folder(gcs_client: Client, bucket_name: str, prefix: str):
    """
    Enumerates blobs within a bucket and batch delete

    Parameters
    ----------
    gcs_client: Client
        The Google Cloud Storage client
    bucket_name: str
        GCS bucket name
    prefix: str
        Folder prefix to delete
    """
    bucket = gcs_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    for blob in blobs:
        blob.delete()
