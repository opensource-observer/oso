import asyncio
from typing import Any

import gcsfs
from dagster import (
    AssetExecutionContext,
    AssetSelection,
    Config,
    RunConfig,
    asset,
    define_asset_job,
)
from oso_dagster.factories import AssetFactoryResponse, early_resources_asset_factory
from oso_dagster.resources import GCSFileResource, NessieResource, TrinoResource

K8S_CONFIG: dict[str, Any] = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "1", "memory": "7Gi"},
            "limits": {"memory": "12Gi"},
        },
    },
    "pod_spec_config": {
        "node_selector": {
            "pool_type": "spot",
        },
        "tolerations": [
            {
                "key": "pool_type",
                "operator": "Equal",
                "value": "spot",
                "effect": "NoSchedule",
            }
        ],
    },
}


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


async def delete_iceberg_table(storage_client: gcsfs.GCSFileSystem, path: str, log):
    folder_name = path.split("/")[-1]
    log.info(f"Deleting {folder_name}")
    await storage_client._rm(path, recursive=True)


class NessieGCConfig(Config):
    gcs_bucket: str = "oso-iceberg-usc1"
    trino_schema: str = "sqlmesh__oso"
    catalogs: list[str] = ["iceberg", "iceberg_consumer"]
    concurrency_limit: int = 1
    dry_run: bool = False


class NessieTagJobConfig(Config):
    # If provided, the `consumer` tag will be updated to point to this hash.
    # Defaults to the latest hash of `main`.
    to_hash: str = ""


default_tag_job_config = RunConfig(
    ops={"nessie__assign_consumer_tag": NessieTagJobConfig()}
)

default_gc_job_config = RunConfig(ops={"nessie__garbage_collect": NessieGCConfig()})


@early_resources_asset_factory()
def nessie_job() -> AssetFactoryResponse:
    @asset(key_prefix="nessie")
    def assign_consumer_tag(nessie: NessieResource, config: NessieTagJobConfig) -> None:
        client = nessie.get_client()
        main_ref = client.get_reference("main")
        consumer_ref = client.get_reference("consumer")

        to_hash = config.to_hash or main_ref.hash_
        client.assign_tag("consumer", main_ref.name, to_hash, consumer_ref.hash_)

    @asset(key_prefix="nessie", op_tags={"dagster-k8s/config": K8S_CONFIG})
    async def garbage_collect(
        context: AssetExecutionContext,
        trino: TrinoResource,
        gcs_file_manager: GCSFileResource,
        config: NessieGCConfig,
    ) -> None:
        async with trino.ensure_available(log_override=context.log):
            async with trino.async_get_client(log_override=context.log) as conn:
                storage_client = gcs_file_manager.get_client()

                try:
                    cur = await conn.cursor()
                    tables_set = set()
                    for catalog in config.catalogs:
                        await cur.execute(
                            f"SHOW TABLES FROM {catalog}.{config.trino_schema}"
                        )
                        tables = await cur.fetchall()
                        context.log.info(f"Found {len(tables)} tables in {catalog}")
                        tables_set.update(t[0] for t in tables)
                    await cur.close()
                    context.log.info(f"Found {len(tables_set)} tables in Trino")

                    folder_paths = await storage_client._ls(
                        f"{config.gcs_bucket}/warehouse/{config.trino_schema}/"
                    )
                    deleted_paths = [
                        path
                        for path in folder_paths
                        if isinstance(path, str)
                        and get_iceberg_table_name(path) not in tables_set
                    ]
                    context.log.info(
                        f"Found {len(deleted_paths)}/{len(folder_paths)} deleted paths"
                    )

                    # Run the delete tasks concurrently with a limit
                    tasks = set()
                    for path in deleted_paths:
                        if config.dry_run:
                            context.log.info(f"Dry run: would delete {path}")
                            continue
                        if len(tasks) >= config.concurrency_limit:
                            # Wait for task to finish before adding a new one
                            _done, tasks = await asyncio.wait(
                                tasks, return_when=asyncio.FIRST_COMPLETED
                            )
                        tasks.add(
                            asyncio.create_task(
                                delete_iceberg_table(storage_client, path, context.log)
                            )
                        )
                    if tasks:
                        await asyncio.wait(tasks)
                    context.log.info(f"Deleted {len(deleted_paths)} paths")
                finally:
                    if storage_client.session:
                        await storage_client.session.close()

    nessie_consumer_tag_job = define_asset_job(
        name="nessie_consumer_tag_job",
        selection=AssetSelection.assets(assign_consumer_tag),
        config=default_tag_job_config,
    )

    nessie_garbage_collect_job = define_asset_job(
        name="nessie_garbage_collect_job",
        selection=AssetSelection.assets(garbage_collect),
        config=default_gc_job_config,
        tags={"opensource.observer/source": "weekly"},
    )

    return AssetFactoryResponse(
        assets=[assign_consumer_tag, garbage_collect],
        jobs=[nessie_consumer_tag_job, nessie_garbage_collect_job],
    )
