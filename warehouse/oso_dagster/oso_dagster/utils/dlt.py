import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from itertools import batched
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    ParamSpec,
    TypeVar,
)

import dagster as dg
from dagster import (
    AssetExecutionContext,
    DefaultSensorStatus,
    OpExecutionContext,
    RunRequest,
    SensorEvaluationContext,
    SensorResult,
    job,
    op,
    sensor,
)
from dlt.sources import DltResource
from google.cloud import bigquery, storage
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)

R = TypeVar("R")
K = ParamSpec("K")


@dataclass(kw_only=True)
class ParallelizeConfig:
    """
    Configuration for the dlt_parallelize decorator.

    Attributes:
        chunk_size (int): Number of tasks per batch.
        parallel_batches (int): Number of batch groups processed in parallel.
        wait_interval (int): Async sleep time (in seconds) after processing each group.
    """

    chunk_size: int
    parallel_batches: int = 10
    wait_interval: int = 5


def dlt_parallelize(config: ParallelizeConfig):
    """
    Decorator that parallelizes the execution of coroutine tasks.

    Args:
        config (ParallelizeConfig): Configuration object
    """

    def _decorator(
        fn: Callable[K, Generator[Callable[..., Coroutine[Any, Any, R]], None, None]],
    ) -> Callable[K, AsyncGenerator[R, None]]:
        """
        Decorator function that wraps the original generator function.

        Args:
            fn (Callable): The original function that yields callables returning coroutine objects.
        """

        async def _wrapper(
            *args: K.args,
            **kwargs: K.kwargs,
        ) -> AsyncGenerator[R, None]:
            """
            Asynchronous wrapper that processes coroutine tasks in parallel and yields results.

            Args:
                *args: Positional arguments forwarded to the original function.
                **kwargs: Keyword arguments forwarded to the original function.
            """

            context = next(
                (arg for arg in args if isinstance(arg, AssetExecutionContext)), None
            )

            log = context.log if context else logger

            chunk_update_fn = None
            if "_chunk_resource_update" in kwargs:
                chunk_update_fn = kwargs.pop("_chunk_resource_update")

            tasks: List[Coroutine[Any, Any, R]] = [
                task() for task in fn(*args, **kwargs)
            ]
            batches_list = list(batched(tasks, config.chunk_size))

            for batch_group in batched(batches_list, config.parallel_batches):
                log.info(
                    f"DLTParallelize: Executing {len(batch_group)} batch(es) in parallel"
                )
                group_coroutines = [coro for batch in batch_group for coro in batch]

                results = []

                for future in asyncio.as_completed(group_coroutines):
                    try:
                        result = await future
                        results.append(result)

                        if not chunk_update_fn:
                            yield result
                    except Exception as e:
                        log.error(f"DLTParallelize: Task failed with exception: {e}")

                log.info(
                    f"DLTParallelize: Waiting for {config.wait_interval} seconds ..."
                )

                if chunk_update_fn and isinstance(chunk_update_fn, Callable):
                    chunk_update_fn(results, len(group_coroutines))

                await asyncio.sleep(config.wait_interval)

        return _wrapper

    return _decorator


T = TypeVar("T")


class ChunkedResourceConfig(Generic[T]):
    """
    Configuration for the process_chunked_resource function. This must
    be used in conjunction with the `dlt_parallelize` decorator.

    Attributes:
        fetch_data_fn (Callable): Function that fetches the data to be chunked.
            It will be called only once if the state file does not exist.
        resource (DltResource): DltResource class to be used for processing the data.
        to_serializable_fn (Callable): Function that converts a single data unit
            to a serializable dictionary. For Pydantic models, this can be the model's
            `model_dump` method.
        destination_table_id (str): BigQuery destination table ID in the format
            'project.dataset.table' where chunked JSONL files will be loaded.
        bq_schema (List[bigquery.SchemaField]): BigQuery schema for the destination table.
            This is used by the BigQuery load job to enforce schema on load.
        gcs_bucket_name (str): Google Cloud Storage bucket name.
        write_disposition (str): BigQuery write disposition (e.g., WRITE_APPEND, WRITE_TRUNCATE).
            Determines how to handle existing data in the table.
        gcs_prefix (str): Google Cloud Storage prefix for chunked data. Defaults
            to "dlt_chunked_state".
        max_age_hours (int): Maximum age in hours for both manifest files and chunk files.
            If the manifest is older than this value, it will be reset and data will be
            re-fetched. Chunk files older than this value will be cleaned up by the sensor.
            This value is stored in the manifest. Defaults to 48 hours.
        context (AssetExecutionContext): Dagster context object.
    """

    def __init__(
        self,
        fetch_data_fn: Callable[[], List[T]],
        resource: DltResource,
        to_serializable_fn: Callable[..., Dict],
        destination_table_id: str,
        bq_schema: List[bigquery.SchemaField],
        gcs_bucket_name: str,
        write_disposition: str,
        gcs_prefix: str = "dlt_chunked_state",
        max_age_hours: int = 48,
        context: AssetExecutionContext | None = None,
    ):
        self.fetch_data_fn = fetch_data_fn
        self.resource = resource
        self.to_serializable_fn = to_serializable_fn
        self.destination_table_id = destination_table_id
        self.bq_schema = bq_schema
        self.gcs_bucket_name = gcs_bucket_name
        self.write_disposition = write_disposition
        self.gcs_prefix = gcs_prefix
        self.max_age_hours = max_age_hours
        self.context = context


def process_chunked_resource(
    config: ChunkedResourceConfig[T],
    /,
    *args,
    **kwargs,
) -> Generator[DltResource, None, None]:
    """
    Processes data in chunks, uploads JSONL files to GCS, and loads them to BigQuery.
    Exposes `_chunk_resource_update` via kwargs for updating state after successful processing.

    Example:
    ```
    @dlt.resource(name="example", ...)
    def resource(pending_items: List, *args, **kwargs):
        for item in pending_items:
            data: List = get_data(item)
            yield data
            kwargs["_chunk_resource_update"]([data])

    @dlt_factory(...)
    def example(
        context: AssetExecutionContext,
        global_config: ResourceParam[DagsterConfig]
    ):
        # Convert dlt columns to BigQuery schema
        from oso_dagster.factories import pydantic_to_dlt_nullable_columns
        from oso_dagster.utils.dlt import dlt_columns_to_bq_schema

        dlt_cols = pydantic_to_dlt_nullable_columns(MyModel)
        bq_schema = dlt_columns_to_bq_schema(dlt_cols)

        return process_chunked_resource(
            ChunkedResourceConfig(
                fetch_data_fn=fetch_fn,
                resource=resource,
                to_serializable_fn=methodcaller("model_dump"),
                destination_table_id="project.dataset.table",
                bq_schema=bq_schema,
                gcs_bucket_name=global_config.gcs_bucket,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                context=context,
            ),
            ...,
        )
    ```

    Args:
        config (ChunkedResourceConfig): Configuration object.
        *args: Positional arguments forwarded to the resource constructor.
        **kwargs: Keyword arguments forwarded to the resource constructor.

    Yields:
        DltResource: The bound resource object.
    """

    storage_client = storage.Client()
    bq_client = bigquery.Client()
    bucket = storage_client.get_bucket(config.gcs_bucket_name)
    state_blob = bucket.blob(f"{config.gcs_prefix}/{config.resource.name}/state.json")

    log = config.context.log if config.context else logger

    log.info(f"ChunkedResource: Checking state in {state_blob.name}")

    def resource_update(elements: List[List], count: int):
        """
        Updates the state manifest and uploads the chunked data to GCS.

        Args:
            elements (List[List]): Elements to be stored in GCS
        """

        current_manifest = state_blob.download_as_string()
        current_data = json.loads(current_manifest)

        current_data["pending_data"] = current_data["pending_data"][count:]
        current_data["updated_at"] = datetime.now().isoformat()

        log.info(
            f"ChunkedResource: Updating state with {len(current_data['pending_data'])} pending entries"
        )

        state_blob.upload_from_string(json.dumps(current_data))

        chunk_id = str(uuid.uuid4())
        load_id = str(time.time())

        serialized_elems = []
        for elem in (
            config.to_serializable_fn(e) for sublist in elements for e in sublist
        ):
            elem["_dlt_load_id"] = load_id
            elem["_dlt_id"] = f"$${chunk_id}"
            serialized_elems.append(elem)

        new_blob = bucket.blob(
            f"{config.gcs_prefix}/{config.resource.name}/chunk.{chunk_id}.jsonl"
        )

        jsonl_content = "\n".join(
            json.dumps(elem, default=str) for elem in serialized_elems
        )
        new_blob.upload_from_string(jsonl_content)

        log.info(f"ChunkedResource: Uploaded {count} elements to {new_blob.name}")

        if not current_data["pending_data"]:
            log.info("ChunkedResource: All chunks uploaded, firing BigQuery load job")
            job_id = fire_load_job()

            current_data["load_job_id"] = job_id
            current_data["updated_at"] = datetime.now().isoformat()
            state_blob.upload_from_string(json.dumps(current_data))

            log.info(f"ChunkedResource: Started load job {job_id}")
            success = wait_for_load_job(job_id)

            if success:
                log.info("ChunkedResource: Load job completed successfully")
                current_data["pending_data"] = []
                state_blob.upload_from_string(json.dumps(current_data))
            else:
                raise RuntimeError(f"BigQuery load job {job_id} failed")

    def fire_load_job() -> str:
        """Fires a BigQuery load job for all JSONL files."""
        uri_pattern = f"gs://{config.gcs_bucket_name}/{config.gcs_prefix}/{config.resource.name}/chunk.*.jsonl"

        job_config = bigquery.LoadJobConfig(
            schema=config.bq_schema,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=config.write_disposition,
        )

        log.info(
            f"ChunkedResource: Starting load job from {uri_pattern} to {config.destination_table_id}"
        )

        load_job = bq_client.load_table_from_uri(
            uri_pattern,
            config.destination_table_id,
            job_config=job_config,
        )

        if not load_job.job_id:
            raise RuntimeError("Failed to start BigQuery load job")

        return load_job.job_id

    def wait_for_load_job(job_id: str) -> bool:
        """Waits for a BigQuery load job to complete and returns success status."""
        log.info(f"ChunkedResource: Waiting for load job {job_id}")

        try:
            job = bq_client.get_job(job_id)
            job.result()
            log.info(f"ChunkedResource: Load job {job_id} completed successfully")
            return True
        except Exception as e:
            log.error(f"ChunkedResource: Load job {job_id} failed: {e}")
            return False

    def check_and_handle_load_job(job_id: str) -> bool:
        """
        Checks the status of a load job and handles it appropriately.
        Returns True if job completed successfully, False if failed.
        Waits for completion if job is still running.
        """
        log.info(f"ChunkedResource: Checking status of load job {job_id}")

        try:
            job = bq_client.get_job(job_id)

            if not job.done():
                log.info(
                    f"ChunkedResource: Load job {job_id} is still running, waiting..."
                )
                job.result()

            if job.errors:
                log.error(
                    f"ChunkedResource: Load job {job_id} failed with errors: {job.errors}"
                )
                return False

            log.info(f"ChunkedResource: Load job {job_id} completed successfully")
            return True

        except Exception as e:
            log.error(f"ChunkedResource: Error checking load job {job_id}: {e}")
            return False

    kwargs["_chunk_resource_update"] = resource_update

    try:
        if not state_blob.exists():
            raise NotFound("State file does not exist")

        manifest = state_blob.download_as_string()
        manifest_data = json.loads(manifest)

        log.info("ChunkedResource: Found existing state manifest")

        max_age_seconds = config.max_age_hours * 60 * 60
        updated_age = (
            datetime.now() - datetime.fromisoformat(manifest_data["updated_at"])
        ).total_seconds()
        created_age = (
            datetime.now() - datetime.fromisoformat(manifest_data["created_at"])
        ).total_seconds()

        if updated_age > max_age_seconds or created_age > max_age_seconds:
            log.info("ChunkedResource: State manifest is too old, resetting")
            manifest_data = None

        if manifest_data and "load_job_id" in manifest_data:
            job_id = manifest_data["load_job_id"]
            log.info(f"ChunkedResource: Found existing load job {job_id}")

            success = check_and_handle_load_job(job_id)

            if success:
                log.info("ChunkedResource: Previous load job completed successfully")
                manifest_data["pending_data"] = []
                state_blob.upload_from_string(json.dumps(manifest_data))
            else:
                log.error("ChunkedResource: Previous load job failed, will retry")
                del manifest_data["load_job_id"]
                state_blob.upload_from_string(json.dumps(manifest_data))
                raise RuntimeError(f"BigQuery load job {job_id} failed")

    except (NotFound, json.JSONDecodeError):
        log.info("ChunkedResource: No existing state found, creating new manifest")
        manifest_data = None

    if manifest_data is None:
        log.info("ChunkedResource: Processing input data")

        manifest_data = {
            "updated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "pending_data": config.fetch_data_fn(),
            "max_age_hours": config.max_age_hours,
        }

        log.info("ChunkedResource: Uploading initial manifest")
        state_blob.upload_from_string(json.dumps(manifest_data))

    if manifest_data["pending_data"]:
        yield config.resource(
            manifest_data["pending_data"],
            *args,
            **kwargs,
        )
    else:
        log.info("ChunkedResource: No pending data to process")

        if "load_job_id" in manifest_data:
            job_id = manifest_data["load_job_id"]
            log.info(
                f"ChunkedResource: Found existing load job {job_id}, verifying status"
            )

            success = check_and_handle_load_job(job_id)

            if not success:
                log.error(f"ChunkedResource: Load job {job_id} failed, will retry")
                del manifest_data["load_job_id"]
                state_blob.upload_from_string(json.dumps(manifest_data))
                raise RuntimeError(f"BigQuery load job {job_id} failed")

            log.info("ChunkedResource: Load job completed, nothing more to do")
        else:
            log.info(
                "ChunkedResource: No load job ID found, checking for orphaned chunks"
            )

            chunk_prefix = f"{config.gcs_prefix}/{config.resource.name}/chunk."
            chunks = list(bucket.list_blobs(prefix=chunk_prefix))

            if chunks:
                log.warning(
                    f"ChunkedResource: Found {len(chunks)} orphaned chunk files, firing load job"
                )
                job_id = fire_load_job()

                manifest_data["load_job_id"] = job_id
                manifest_data["updated_at"] = datetime.now().isoformat()
                state_blob.upload_from_string(json.dumps(manifest_data))

                log.info(f"ChunkedResource: Started load job {job_id}")
                success = wait_for_load_job(job_id)

                if success:
                    log.info("ChunkedResource: Orphaned chunks loaded successfully")
                    state_blob.upload_from_string(json.dumps(manifest_data))
                else:
                    raise RuntimeError(f"BigQuery load job {job_id} failed")
            else:
                log.info("ChunkedResource: No orphaned chunks found, nothing to do")

        yield config.resource([], *args, **kwargs)


CHUNKED_STATE_JOB_CONFIG = {
    "dagster-k8s/config": {
        "merge_behavior": "SHALLOW",
        "container_config": {
            "resources": {
                "requests": {
                    "cpu": "250m",
                    "memory": "1024Mi",
                },
                "limits": {
                    "memory": "2048Mi",
                },
            },
        },
        "pod_spec_config": {
            "node_selector": {
                "pool_type": "persistent",
            },
            "tolerations": [
                {
                    "key": "pool_type",
                    "operator": "Equal",
                    "value": "persistent",
                    "effect": "NoSchedule",
                }
            ],
        },
    },
}


async def batch_delete_blobs(
    context: OpExecutionContext, bucket: storage.Bucket, blob_names: List[str]
):
    """
    Asynchronous batch delete function that deletes blobs from a GCS bucket.

    Args:
        context (OpExecutionContext): The Dagster operation context
        bucket (storage.Bucket): The GCS bucket object
        blob_names (List[str]): Names of blobs to delete
    """

    if not blob_names:
        context.log.info("No blobs to delete, skipping batch delete operation")
        return

    delete_tasks = []

    for batch in batched(blob_names, 100):
        if not batch:
            continue

        async def delete_batch(names):
            if not names:
                return

            context.log.info(f"Deleting batch of {len(names)} blobs")
            for name in names:
                try:
                    bucket.blob(name).delete()
                except Exception as e:
                    context.log.error(f"Error deleting blob {name}: {e}")

        delete_tasks.append(delete_batch(batch))

    if delete_tasks:
        await asyncio.gather(*delete_tasks)
    else:
        context.log.info("No delete tasks created, all batches were empty")


async def cleanup_chunks(
    context: OpExecutionContext,
    bucket_name: str,
    prefix: str = "dlt_chunked_state",
    client: Optional[storage.Client] = None,
):
    """
    Cleanup function that deletes chunk files older than the specified age.
    Also cleans up state files if they have no pending data.
    The max_age_hours is read from each resource's manifest, falling back to
    48 hours if not specified.

    Args:
        context (OpExecutionContext): The Dagster operation context
        bucket_name (str): The GCS bucket name
        prefix (str): The GCS prefix
        client (storage.Client): Optional storage client
    """

    DEFAULT_MAX_AGE_HOURS = 48

    if client is None:
        client = storage.Client()

    bucket = client.get_bucket(bucket_name)

    context.log.info(
        f"Scanning for chunk files in bucket '{bucket_name}' with prefix '{prefix}'"
    )

    blobs = list(bucket.list_blobs(prefix=prefix))

    chunk_blobs = [
        blob
        for blob in blobs
        if "chunk." in blob.name
        and (blob.name.endswith(".jsonl") or blob.name.endswith(".json"))
    ]

    context.log.info(f"Found {len(chunk_blobs)} chunk files")

    resource_chunks = {}
    for blob in chunk_blobs:
        parts = blob.name.split("/")
        if len(parts) >= 2:
            resource_name = parts[-2]
            if resource_name not in resource_chunks:
                resource_chunks[resource_name] = []
            resource_chunks[resource_name].append(blob)

    context.log.info(f"Found chunks for {len(resource_chunks)} resources")

    cleanup_tasks = []
    total_deleted = 0

    state_blobs = [blob for blob in blobs if blob.name.endswith("/state.json")]

    resource_max_age = {}
    for state_blob in state_blobs:
        try:
            state_data = json.loads(state_blob.download_as_string())

            parts = state_blob.name.split("/")
            if len(parts) >= 2:
                resource_name = parts[-2]
                resource_max_age[resource_name] = state_data.get(
                    "max_age_hours", DEFAULT_MAX_AGE_HOURS
                )
                context.log.info(
                    f"Resource '{resource_name}' max_age_hours: {resource_max_age[resource_name]}"
                )

            if not state_data.get("pending_data"):
                context.log.info(
                    f"State file {state_blob.name} has no pending data, marking for deletion"
                )
                cleanup_tasks.append(
                    batch_delete_blobs(context, bucket, [state_blob.name])
                )
                total_deleted += 1
        except Exception as e:
            context.log.error(f"Error processing state file {state_blob.name}: {e}")

    for resource_name, blobs in resource_chunks.items():
        max_age_hours = resource_max_age.get(resource_name, DEFAULT_MAX_AGE_HOURS)

        context.log.info(
            f"Processing resource: {resource_name} with {len(blobs)} chunk files "
            f"(max_age_hours: {max_age_hours})"
        )

        blobs_to_delete = []
        for blob in blobs:
            blob_updated = blob.updated
            age_hours = (
                datetime.now() - blob_updated.replace(tzinfo=None)
            ).total_seconds() / 3600

            if age_hours > max_age_hours:
                context.log.info(
                    f"Marking chunk for deletion: {blob.name} (age: {age_hours:.1f} hours)"
                )
                blobs_to_delete.append(blob.name)
            else:
                context.log.info(
                    f"Chunk is too young to delete: {blob.name} (age: {age_hours:.1f} hours)"
                )

        if blobs_to_delete:
            context.log.info(
                f"Scheduling deletion of {len(blobs_to_delete)} chunks for {resource_name}"
            )
            cleanup_tasks.append(batch_delete_blobs(context, bucket, blobs_to_delete))
            total_deleted += len(blobs_to_delete)
        else:
            context.log.info(f"No chunks to delete for {resource_name}")

    context.log.info(f"Total files marked for deletion: {total_deleted}")

    if cleanup_tasks:
        context.log.info(f"Executing {len(cleanup_tasks)} cleanup tasks")
        await asyncio.gather(*cleanup_tasks)
        context.log.info(f"Successfully executed {len(cleanup_tasks)} cleanup tasks")
    else:
        context.log.info("No cleanup tasks to execute")


def setup_chunked_state_cleanup_sensor(
    gcs_bucket_name: str,
    gcs_prefix: str = "dlt_chunked_state",
    enable: bool = False,
):
    """
    Sets up a sensor and job to clean up chunk files based on per-asset max_age_hours
    configuration stored in each resource's manifest.

    Args:
        gcs_bucket_name (str): GCS bucket name
        gcs_prefix (str): GCS prefix for chunked data
        enable (bool): Whether to enable the sensor

    Returns:
        AssetFactoryResponse: Response containing sensors and jobs
    """
    from oso_dagster.factories.common import AssetFactoryResponse

    @op(name="chunked_state_cleanup_op")
    async def cleanup_op(context: OpExecutionContext) -> None:
        context.log.info(
            f"Starting chunked state cleanup job with settings:"
            f"\n  - Bucket: {gcs_bucket_name}"
            f"\n  - Prefix: {gcs_prefix}"
        )

        await cleanup_chunks(
            context=context,
            bucket_name=gcs_bucket_name,
            prefix=gcs_prefix,
        )

        context.log.info("Chunked state cleanup job completed successfully")

    @job(name="chunked_state_cleanup_job", executor_def=dg.in_process_executor)
    def cleanup_job():
        cleanup_op()

    status = DefaultSensorStatus.RUNNING if enable else DefaultSensorStatus.STOPPED

    @sensor(
        name="chunked_state_cleanup_sensor",
        job=cleanup_job,
        minimum_interval_seconds=60 * 60 * 2,
        default_status=status,
    )
    def cleanup_sensor(context: SensorEvaluationContext):
        """
        Sensor that periodically triggers the job to clean up chunk files.
        The max age for each resource is read from its manifest.
        """
        context.log.info("Evaluating chunked state cleanup sensor")

        return SensorResult(
            run_requests=[
                RunRequest(
                    run_key=f"chunked-state-cleanup-{context.cursor or 'initial'}",
                    tags=CHUNKED_STATE_JOB_CONFIG,
                )
            ],
            cursor=str(int(datetime.now().timestamp())),
        )

    return AssetFactoryResponse(
        [],
        sensors=[cleanup_sensor],
        jobs=[cleanup_job],
    )


def dlt_columns_to_bq_schema(
    dlt_columns: Dict,
    extra_fields: Optional[List[bigquery.SchemaField]] = None,
) -> List[bigquery.SchemaField]:
    """
    Converts dlt table schema columns to BigQuery SchemaField list.

    Args:
        dlt_columns (Dict): Dictionary of dlt columns from pydantic_to_dlt_nullable_columns
        extra_fields (Optional[List[bigquery.SchemaField]]): Additional fields to append to schema

    Returns:
        List[bigquery.SchemaField]: List of BigQuery SchemaField objects
    """

    type_mapping = {
        "text": "STRING",
        "varchar": "STRING",
        "string": "STRING",
        "bigint": "INT64",
        "integer": "INT64",
        "int": "INT64",
        "double": "FLOAT64",
        "float": "FLOAT64",
        "decimal": "NUMERIC",
        "bool": "BOOL",
        "boolean": "BOOL",
        "timestamp": "TIMESTAMP",
        "date": "DATE",
        "time": "TIME",
        "binary": "BYTES",
        "json": "JSON",
        "complex": "JSON",
    }

    schema_fields = []

    for column_name, column_def in dlt_columns.items():
        data_type = column_def.get("data_type", "STRING")

        bq_type = type_mapping.get(data_type.lower(), "STRING")

        nullable = column_def.get("nullable", True)
        mode = "NULLABLE" if nullable else "REQUIRED"

        schema_fields.append(
            bigquery.SchemaField(
                name=column_name,
                field_type=bq_type,
                mode=mode,
            )
        )

    if extra_fields:
        schema_fields.extend(extra_fields)

    return schema_fields
