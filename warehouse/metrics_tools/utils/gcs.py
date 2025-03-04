import asyncio
import logging
import typing as t

import aiohttp
import aiohttp.client_exceptions
from gcloud.aio import storage

logger = logging.getLogger(__name__)


async def delete_gcs_folders(
    client: storage.Storage,
    bucket_name: str,
    folders: t.List[str],
):
    bucket = storage.Bucket(client, bucket_name)
    for folder in folders:
        await delete_gcs_folder(client, bucket, folder)


async def delete_gcs_folder(
    client: storage.Storage,
    bucket: storage.Bucket,
    folder: str,
):
    blobs = await list_gcs_blobs(bucket, folder)
    await delete_gcs_blobs(client, bucket, blobs)


async def list_gcs_blobs(
    bucket: storage.Bucket,
    folder: str,
) -> t.List[str]:
    blobs = await bucket.list_blobs(prefix=folder)
    return blobs


async def delete_gcs_blobs(
    client: storage.Storage,
    bucket: storage.Bucket,
    files: t.List[str],
    retries: int = 3,
):
    async def delete(
        semaphore: asyncio.Semaphore,
        client: storage.Storage,
        blob: str,
        retries: int,
        dry_run: bool,
    ):
        async with semaphore:
            logger.info(f"Deleting: {blob}")
            if not dry_run:
                for _ in range(3):
                    try:
                        await asyncio.wait_for(
                            client.delete(bucket.name, blob), timeout=10
                        )
                        break
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout deleting: {blob}")
                    except aiohttp.client_exceptions.ClientResponseError as e:
                        if e.status >= 500 and e.status < 600:
                            logger.error(f"Server error deleting: {blob}, {e}")
                        else:
                            raise e
            else:
                logger.info(f"Would have deleted: {blob}")

    semaphre = asyncio.Semaphore(1000)
    delete_tasks: t.List[asyncio.Task] = []

    for blob in files:
        delete_task = asyncio.create_task(
            delete(semaphre, client, blob, retries, False)
        )
        delete_tasks.append(delete_task)

    try:
        await asyncio.gather(*delete_tasks)
    except Exception as e:
        logger.error(f"Error deleting blobs: {e}")
