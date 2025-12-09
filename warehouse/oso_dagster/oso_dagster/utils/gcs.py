import typing as t

from google.cloud.storage import Client

from .errors import MalformedUrl

GCS_URL_PREFIX = "gs://"


def gcs_to_http_url(gcs_path: str) -> str:
    """
    Converts a `gs://` url to a `https://storage.googleapis.com/` url

    Parameters
    ----------
    gcs_path: str
        URL prefixed with gs://

    Returns
    -------
    str
        HTTPS URL to the GCS object
    """
    if not gcs_path.startswith(GCS_URL_PREFIX):
        raise MalformedUrl(f"Expected gs:// prefix in {gcs_path}")
    return gcs_path.replace("gs://", "https://storage.googleapis.com/")


def gcs_to_bucket_name(gcs_path: str) -> str:
    """
    Converts a `gs://` to just the name of the bucket in the url
    """
    if not gcs_path.startswith(GCS_URL_PREFIX):
        raise MalformedUrl(f"Expected gs:// prefix in {gcs_path}")
    return gcs_path[len(GCS_URL_PREFIX) :]


def batch_delete_blobs(
    gcs_client: Client,
    bucket_name: str,
    blobs: t.List[str],
    batch_size: int,
    user_project: t.Optional[str] = None,
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
    bucket = gcs_client.bucket(bucket_name, user_project=user_project)

    batch: t.List[str] = []
    for blob in blobs:
        batch.append(blob)
        if len(batch) == batch_size:
            # TODO: is this a bug? Should we reset the batch?
            bucket.delete_blobs(blobs=batch)
    if len(batch) > 0:
        bucket.delete_blobs(blobs=batch)


def batch_delete_folder(
    gcs_client: Client,
    bucket_name: str,
    prefix: str,
    user_project: t.Optional[str] = None,
):
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
    bucket = gcs_client.bucket(bucket_name, user_project=user_project)
    blobs = bucket.list_blobs(prefix=prefix)
    for blob in blobs:
        blob.delete()
