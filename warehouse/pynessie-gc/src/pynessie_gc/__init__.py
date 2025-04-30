import asyncio
import os

import aiotrino
import gcsfs

GOOGLE_PROJECT = os.environ.get("GOOGLE_PROJECT", "opensource-observer")
BUCKET = os.environ.get("BUCKET_NAME", "oso-iceberg-usc1")
TRINO_HOST = os.environ.get("TRINO_HOST", "localhost")
TRINO_PORT = os.environ.get("TRINO_PORT", "8080")
TRINO_SCHEMA = os.environ.get("TRINO_SCHEMA", "sqlmesh__oso")

CONCURRENCY_LIMIT = int(os.environ.get("CONCURRENCY_LIMIT", "10"))

def get_iceberg_table_name(path: str) -> str:
    parts = path.split("/")
    table_name_with_uuid = parts[-1]
    parts = table_name_with_uuid.split("__")
    if len(parts) > 1:  # If there are double underscores
        last_part = parts[-1]
        # Split the last part by the last single underscore
        if "_" in last_part:
            last_part_without_uuid = last_part.rsplit("_", 1)[0]
            parts[-1] = last_part_without_uuid
    table_name = "__".join(parts)
    return table_name


async def delete_iceberg_table(storage_client: gcsfs.GCSFileSystem, path: str):
    folder_name = path.split("/")[-1]
    print(f"Deleting {folder_name}")
    await storage_client._rm(path, recursive=True)


async def _main():
    trino_client = aiotrino.dbapi.connect(
        host=TRINO_HOST, port=TRINO_PORT, user="trino", request_timeout=180
    )
    storage_client = gcsfs.GCSFileSystem(project=GOOGLE_PROJECT, asynchronous=True)

    try:
        cur = await trino_client.cursor()
        await cur.execute(f"SHOW TABLES FROM iceberg.{TRINO_SCHEMA}")
        tables = await cur.fetchall()
        tables_set = set([t[0] for t in tables])
        await cur.close()

        folder_paths = await storage_client._ls(f"{BUCKET}/warehouse/{TRINO_SCHEMA}/")
        deleted_paths = [
            path
            for path in folder_paths
            if isinstance(path, str) and get_iceberg_table_name(path) not in tables_set
        ]
        print(f"Found {len(deleted_paths)}/{len(folder_paths)} deleted paths")

        # Run the delete tasks concurrently with a limit
        tasks = set()
        for path in deleted_paths:
            if len(tasks) >= CONCURRENCY_LIMIT:
                # Wait for task to finish before adding a new one
                _done, tasks = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
            tasks.add(asyncio.create_task(delete_iceberg_table(storage_client, path)))
        await asyncio.wait(tasks)
    finally:
        await trino_client.close()
        if storage_client.session:
            await storage_client.session.close()


def main() -> None:
    asyncio.run(_main())
