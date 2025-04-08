import asyncio
import json
import logging
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
from google.cloud import storage
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
    Decorator that parallelizes the execution of coroutine tasks. It processes
    coroutine tasks in parallel and yields results.

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

            retrieve_failed_fn = None
            if "_chunk_retrieve_failed" in kwargs:
                retrieve_failed_fn = kwargs.pop("_chunk_retrieve_failed")

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
                        results.append(await future)
                    except Exception as e:
                        log.error(f"DLTParallelize: Task failed with exception: {e}")

                log.info(
                    f"DLTParallelize: Waiting for {config.wait_interval} seconds ..."
                )

                if chunk_update_fn and isinstance(chunk_update_fn, Callable):
                    chunk_update_fn(results, len(group_coroutines))

                await asyncio.sleep(config.wait_interval)

            if retrieve_failed_fn and isinstance(retrieve_failed_fn, Callable):
                for retrieved in retrieve_failed_fn():
                    yield retrieved

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
        gcs_bucket_name (str): Google Cloud Storage bucket name.
        gcs_prefix (str): Google Cloud Storage prefix for chunked data. Defaults
            to "dlt_chunked_state".
        max_manifest_age (int): Maximum age of the manifest file in seconds. If the
            manifest file is older than this value, the manifest will be reset. This
            means that the `fetch_data_fn` will be called again, re-fetching all the
            data and starting from scratch. Defaults to 3 days.
        context (AssetExecutionContext): Dagster context object.
    """

    def __init__(
        self,
        fetch_data_fn: Callable[[], List[T]],
        resource: DltResource,
        to_serializable_fn: Callable[..., Dict],
        gcs_bucket_name: str,
        gcs_prefix: str = "dlt_chunked_state",
        max_manifest_age: int = 60 * 60 * 24 * 3,
        context: AssetExecutionContext | None = None,
    ):
        self.fetch_data_fn = fetch_data_fn
        self.resource = resource
        self.to_serializable_fn = to_serializable_fn
        self.gcs_bucket_name = gcs_bucket_name
        self.gcs_prefix = gcs_prefix
        self.max_manifest_age = max_manifest_age
        self.context = context


def process_chunked_resource(
    config: ChunkedResourceConfig[T],
    /,
    *args,
    **kwargs,
) -> Generator[DltResource, None, None]:
    """
    This function configures a DLT resource to keep state checkpoints in Google Cloud Storage.
    It processes the data in chunks and yields the resource object. It also exposes two
    functions via the kwargs: `_chunk_resource_update` and `_chunk_retrieve_failed`.

    The `_chunk_resource_update` function is used to update the state manifest and upload
    the chunked data to GCS.
    The `_chunk_retrieve_failed` function is used to retrieve all the stored chunks in GCS
    which failed in previous runs.

    The decorated function must use these functions to update the state manifest and upload
    the chunked data to GCS. It must call `_chunk_resource_update` with the elements to be
    uploaded to GCS after a successful yield. It must also call `_chunk_retrieve_failed` at the
    end of the function to retrieve all the stored chunks in GCS which failed in previous runs.

    Example:
    ```
    @dlt.resource(name="example", ...)
    def resource(max: int, *args, **kwargs):
        for i in range(max):
            data: List = get_data(i)
            yield data

            # Update the state manifest and upload the data
            kwargs["_chunk_resource_update"]([data])

        # Retrieve all the stored chunks in GCS from previous runs
        yield from kwargs["_chunk_retrieve_failed"]()

    @dlt_factory(...)
    def example(
        context: AssetExecutionContext,
        global_config: ResourceParam[DagsterConfig]
    ):
    ...

    return process_chunked_resource(
        ChunkedResourceConfig(
            fetch_data_fn=fetch_fn,
            resource=resource,
            to_serializable_fn=methodcaller("model_dump"),
            gcs_bucket_name=global_config.gcs_bucket,
            context=context,
        ),
        ..., # these will be forwarded to `resource`
    )
    ```

    Args:
        config (ChunkedResourceConfig): Configuration object.
        *args: Positional arguments forwarded to the resource constructor.
        **kwargs: Keyword arguments forwarded to the resource constructor.

    Yields:
        DltResource: The bound resource object.
    """

    client = storage.Client()
    bucket = client.get_bucket(config.gcs_bucket_name)
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

        serialized_elems = [
            config.to_serializable_fn(elem) for sublist in elements for elem in sublist
        ]

        new_blob = bucket.blob(
            f"{config.gcs_prefix}/{config.resource.name}/chunk.{uuid.uuid4()}.json"
        )

        new_blob.upload_from_string(json.dumps(serialized_elems, default=str))

        log.info(f"ChunkedResource: Uploaded {count} elements to {new_blob.name}")

        if not current_data["pending_data"]:
            log.info("ChunkedResource: No more pending data to process")

    def retrieve_failed():
        """
        Retrieves all the stored chunks in GCS which failed in previous runs.
        Does NOT delete the blobs - this will be handled by the cleanup sensor.

        Yields:
            Dict: The retrieved chunked data
        """

        blobs = bucket.list_blobs(
            prefix=f"{config.gcs_prefix}/{config.resource.name}/chunk."
        )

        for blob in blobs:
            if blob.name.endswith(".json"):
                log.info(f"ChunkedResource: Retrieving chunk {blob.name}")
                yield from json.loads(blob.download_as_string())

    kwargs["_chunk_retrieve_failed"] = retrieve_failed

    try:
        if not state_blob.exists():
            raise NotFound("State file does not exist")

        manifest = state_blob.download_as_string()
        manifest_data = json.loads(manifest)

        log.info("ChunkedResource: Found existing state manifest")

        if (
            datetime.now() - datetime.fromisoformat(manifest_data["updated_at"])
            or datetime.now() - datetime.fromisoformat(manifest_data["created_at"])
        ).total_seconds() > config.max_manifest_age:
            log.info("ChunkedResource: State manifest is too old, resetting")
            manifest_data = None

    except (NotFound, json.JSONDecodeError):
        log.info("ChunkedResource: No existing state found, creating new manifest")

        manifest_data = {
            "updated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "pending_data": config.fetch_data_fn(),
        }

        state_blob.upload_from_string(json.dumps(manifest_data))

    if manifest_data is None:
        log.info("ChunkedResource: Processing input data")

        manifest_data = {
            "updated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "pending_data": config.fetch_data_fn(),
        }

        log.info("ChunkedResource: Uploading initial manifest")
        state_blob.upload_from_string(json.dumps(manifest_data))

    kwargs["_chunk_resource_update"] = resource_update

    yield config.resource(
        manifest_data["pending_data"],
        *args,
        **kwargs,
    )


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
    max_age_hours: int = 24,
    client: Optional[storage.Client] = None,
):
    """
    Cleanup function that deletes chunk files older than the specified age.
    Also cleans up state files if they have no pending data.

    Args:
        context (OpExecutionContext): The Dagster operation context
        bucket_name (str): The GCS bucket name
        prefix (str): The GCS prefix
        max_age_hours (int): The maximum age of chunk files to clean up
        client (storage.Client): Optional storage client
    """

    if client is None:
        client = storage.Client()

    bucket = client.get_bucket(bucket_name)

    context.log.info(
        f"Scanning for chunk files in bucket '{bucket_name}' with prefix '{prefix}'"
    )

    blobs = list(bucket.list_blobs(prefix=prefix))

    chunk_blobs = [
        blob for blob in blobs if "chunk." in blob.name and blob.name.endswith(".json")
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

    for state_blob in state_blobs:
        try:
            state_data = json.loads(state_blob.download_as_string())
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
        context.log.info(
            f"Processing resource: {resource_name} with {len(blobs)} chunk files"
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
    max_age_hours: int = 48,
    enable: bool = True,
):
    """
    Sets up a sensor and job to clean up chunk files that are older than the specified age.

    Args:
        gcs_bucket_name (str): GCS bucket name
        gcs_prefix (str): GCS prefix for chunked data
        max_age_hours (int): Maximum age in hours for chunk files
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
            f"\n  - Max age for chunk files: {max_age_hours} hours"
        )

        await cleanup_chunks(
            context=context,
            bucket_name=gcs_bucket_name,
            prefix=gcs_prefix,
            max_age_hours=max_age_hours,
        )

        context.log.info("Chunked state cleanup job completed successfully")

    @job(name="chunked_state_cleanup_job")
    def cleanup_job():
        cleanup_op()

    status = DefaultSensorStatus.RUNNING if enable else DefaultSensorStatus.STOPPED

    @sensor(
        name="chunked_state_cleanup_sensor",
        job=cleanup_job,
        minimum_interval_seconds=60 * 60 * 12,
        default_status=status,
    )
    def cleanup_sensor(context: SensorEvaluationContext):
        """
        Sensor that periodically triggers the job to clean up chunk files
        that are older than the specified age.
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
