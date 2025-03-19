import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from itertools import batched
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Coroutine,
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
                        result = await future
                        results.append(result)
                    except Exception as e:
                        log.error(f"DLTParallelize: Task failed with exception: {e}")

                for result in results:
                    yield result

                log.info(
                    f"DLTParallelize: Waiting for {config.wait_interval} seconds ..."
                )

                if chunk_update_fn and isinstance(chunk_update_fn, Callable):
                    chunk_update_fn(results)

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
        serialize_item_fn (Callable): Function that converts a single data unit
            to a serializable representation. For Pydantic models, this can be the model's
            `model_dump` method, which returns a dictionary.
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
        serialize_item_fn: Callable[..., dict],
        gcs_bucket_name: str,
        gcs_prefix: str = "dlt_chunked_state",
        max_manifest_age: int = 60 * 60 * 24 * 3,
        context: AssetExecutionContext | None = None,
    ):
        self.fetch_data_fn = fetch_data_fn
        self.resource = resource
        self.serialize_item_fn = serialize_item_fn
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
    processing_flag_blob = bucket.blob(
        f"{config.gcs_prefix}/{config.resource.name}/processing_flag.json"
    )

    log = config.context.log if config.context else logger

    log.info(f"ChunkedResource: Checking state in {state_blob.name}")

    processing_flag_blob.upload_from_string(
        json.dumps({"started_at": datetime.now().isoformat(), "status": "running"})
    )

    def resource_update(elements: List[List]):
        """
        Updates the state manifest and uploads the chunked data to GCS.

        Args:
            elements (List[List]): Elements to be stored in GCS
        """

        count = len(elements)
        try:
            current_manifest = state_blob.download_as_string()
            current_data = json.loads(current_manifest)

            if count > len(current_data["pending_data"]):
                log.warning(
                    f"ChunkedResource: Attempted to process {count} elements but only {len(current_data['pending_data'])} remain"
                )
                count = len(current_data["pending_data"])

            current_data["pending_data"] = current_data["pending_data"][count:]
            current_data["updated_at"] = datetime.now().isoformat()

            log.info(
                f"ChunkedResource: Updating state with {len(current_data['pending_data'])} pending entries"
            )

            temp_state_blob = bucket.blob(
                f"{config.gcs_prefix}/{config.resource.name}/state.temp.json"
            )
            temp_state_blob.upload_from_string(json.dumps(current_data))

            state_blob.upload_from_string(json.dumps(current_data))

            temp_state_blob.delete()

            if not current_data["pending_data"]:
                log.info("ChunkedResource: No more pending data")
                flag_data = json.loads(processing_flag_blob.download_as_string())
                flag_data["status"] = "completed"
                flag_data["updated_at"] = datetime.now().isoformat()
                flag_data["completed_reason"] = "no_pending_data"
                processing_flag_blob.upload_from_string(json.dumps(flag_data))
                log.info(
                    "ChunkedResource: Marked process as completed - all items processed"
                )

            stringified_elems = [
                config.serialize_item_fn(elem)
                for sublist in elements
                for elem in sublist
            ]

            chunk_id = str(uuid.uuid4())
            new_blob = bucket.blob(
                f"{config.gcs_prefix}/{config.resource.name}/chunk.{chunk_id}.json"
            )

            new_blob.upload_from_string(json.dumps(stringified_elems, default=str))

            flag_data = json.loads(processing_flag_blob.download_as_string())
            if "processed_chunks" not in flag_data:
                flag_data["processed_chunks"] = []
            flag_data["processed_chunks"].append(chunk_id)
            flag_data["updated_at"] = datetime.now().isoformat()
            processing_flag_blob.upload_from_string(json.dumps(flag_data))

            log.info(f"ChunkedResource: Uploaded {count} elements to {new_blob.name}")

        except Exception as e:
            log.error(f"ChunkedResource: Failed to update state: {e}")
            processing_flag_blob.upload_from_string(
                json.dumps(
                    {
                        "status": "error",
                        "error": str(e),
                        "updated_at": datetime.now().isoformat(),
                    }
                )
            )
            raise

    def retrieve_failed(yield_elems: bool):
        """
        Retrieves all the stored chunks in GCS which failed in previous runs. If
        `yield_elems` is True, it yields the elements as they are retrieved. Otherwise,
        it works as a cleanup function, marking the process as completed.

        This function will only process chunks if the run is still in progress (not completed or cleaned).

        Args:
            yield_elems (bool): If True, yields the elements as they are retrieved

        Yields:
            Dict: The retrieved chunked data
        """

        blobs = list(
            bucket.list_blobs(
                prefix=f"{config.gcs_prefix}/{config.resource.name}/chunk."
            )
        )

        if not blobs:
            log.info("ChunkedResource: No chunks found to process")

            if not yield_elems:
                try:
                    manifest = state_blob.download_as_string()
                    manifest_data = json.loads(manifest)

                    if not manifest_data["pending_data"]:
                        flag_data = json.loads(
                            processing_flag_blob.download_as_string()
                        )
                        flag_data["status"] = "completed"
                        flag_data["updated_at"] = datetime.now().isoformat()
                        processing_flag_blob.upload_from_string(json.dumps(flag_data))
                        log.info(
                            "ChunkedResource: Marked process as completed (no pending data)"
                        )
                except Exception as e:
                    log.error(
                        f"ChunkedResource: Error checking manifest during cleanup: {e}"
                    )

            return

        chunk_names = []
        retrieved_count = 0

        for blob in blobs:
            chunk_names.append(blob.name)
            if yield_elems and blob.name.endswith(".json"):
                log.info(f"ChunkedResource: Retrieving chunk {blob.name}")
                try:
                    chunk_data = json.loads(blob.download_as_string())
                    retrieved_count += len(chunk_data)
                    yield from chunk_data
                except Exception as e:
                    log.error(
                        f"ChunkedResource: Failed to retrieve chunk {blob.name}: {e}"
                    )

        if yield_elems:
            log.info(
                f"ChunkedResource: Retrieved {retrieved_count} items from {len(chunk_names)} chunks"
            )

        if not yield_elems:
            try:
                manifest = state_blob.download_as_string()
                manifest_data = json.loads(manifest)

                if not manifest_data["pending_data"]:
                    flag_data = json.loads(processing_flag_blob.download_as_string())
                    flag_data["status"] = "completed"
                    flag_data["updated_at"] = datetime.now().isoformat()
                    flag_data["cleaned_chunks_count"] = len(chunk_names)
                    processing_flag_blob.upload_from_string(json.dumps(flag_data))
                    log.info(
                        f"ChunkedResource: Marked process as completed with {len(chunk_names)} chunks processed"
                    )
            except Exception as e:
                log.error(f"ChunkedResource: Failed during status update: {e}")
                processing_flag_blob.upload_from_string(
                    json.dumps(
                        {
                            "status": "error",
                            "phase": "cleanup",
                            "error": str(e),
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                )

    def recover_from_previous_run():
        """
        Attempts to recover from a previous interrupted run

        Returns:
            dict: The manifest data to use
        """
        try:
            if processing_flag_blob.exists():
                flag_data = json.loads(processing_flag_blob.download_as_string())

                if flag_data.get("status") == "error":
                    log.warning(
                        f"ChunkedResource: Previous run failed with error: {flag_data.get('error')}"
                    )
                elif flag_data.get("status") == "running":
                    log.warning(
                        "ChunkedResource: Previous run was interrupted during processing"
                    )
        except Exception as e:
            log.error(f"ChunkedResource: Failed to recover from previous run: {e}")

    recover_from_previous_run()

    kwargs["_chunk_retrieve_failed"] = partial(retrieve_failed, False)

    try:
        if not state_blob.exists():
            raise NotFound("State file does not exist")

        manifest = state_blob.download_as_string()
        manifest_data = json.loads(manifest)

        log.info("ChunkedResource: Found existing state manifest")
        kwargs["_chunk_retrieve_failed"] = partial(retrieve_failed, True)

        temp_state_blob = bucket.blob(
            f"{config.gcs_prefix}/{config.resource.name}/state.temp.json"
        )
        if temp_state_blob.exists():
            log.warning("ChunkedResource: Found temporary state file, using it instead")
            temp_manifest = temp_state_blob.download_as_string()
            manifest_data = json.loads(temp_manifest)
            state_blob.upload_from_string(temp_manifest)
            temp_state_blob.delete()

        manifest_age = max(
            (
                datetime.now() - datetime.fromisoformat(manifest_data["updated_at"])
            ).total_seconds(),
            (
                datetime.now() - datetime.fromisoformat(manifest_data["created_at"])
            ).total_seconds(),
        )

        if manifest_age > config.max_manifest_age:
            log.info("ChunkedResource: State manifest is too old, resetting")
            manifest_data = None
            kwargs["_chunk_retrieve_failed"] = partial(retrieve_failed, False)

            processing_flag_blob.delete()
            processing_flag_blob.upload_from_string(
                json.dumps(
                    {
                        "started_at": datetime.now().isoformat(),
                        "status": "running",
                    }
                )
            )

    except (NotFound, json.JSONDecodeError) as e:
        log.info(
            f"ChunkedResource: No existing state found, creating new manifest: {str(e)}"
        )

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

    processing_flag_blob.upload_from_string(
        json.dumps(
            {
                "status": "processing",
                "updated_at": datetime.now().isoformat(),
                "manifest_entries": len(manifest_data["pending_data"]),
            }
        )
    )

    try:
        yield config.resource(
            manifest_data["pending_data"],
            *args,
            **kwargs,
        )

        try:
            current_manifest = state_blob.download_as_string()
            current_data = json.loads(current_manifest)

            if not current_data["pending_data"]:
                processing_flag_blob.upload_from_string(
                    json.dumps(
                        {
                            "status": "completed",
                            "updated_at": datetime.now().isoformat(),
                        }
                    )
                )
                log.info("ChunkedResource: All data processed, marked as completed")
            else:
                log.info(
                    f"ChunkedResource: Still has {len(current_data['pending_data'])} pending items"
                )

                if kwargs.get("_chunk_retrieve_failed"):
                    log.info("ChunkedResource: Forcing processing of remaining items")
                    processing_flag_blob.upload_from_string(
                        json.dumps(
                            {
                                "status": "recovering",
                                "remaining_items": len(current_data["pending_data"]),
                                "updated_at": datetime.now().isoformat(),
                            }
                        )
                    )

                    retrieve_fn = partial(retrieve_failed, True)
                    for _ in retrieve_fn():
                        pass

                    try:
                        updated_manifest = state_blob.download_as_string()
                        updated_data = json.loads(updated_manifest)

                        if not updated_data["pending_data"]:
                            processing_flag_blob.upload_from_string(
                                json.dumps(
                                    {
                                        "status": "completed",
                                        "updated_at": datetime.now().isoformat(),
                                        "recovery_completed": True,
                                    }
                                )
                            )
                            log.info(
                                "ChunkedResource: Recovery processing completed, marked as completed"
                            )
                        else:
                            log.warning(
                                f"ChunkedResource: After recovery, still has {len(updated_data['pending_data'])} pending items"
                            )
                    except Exception as e:
                        log.error(
                            f"ChunkedResource: Error checking state after recovery: {e}"
                        )

        except Exception as e:
            log.error(f"ChunkedResource: Error checking final state: {e}")

    except Exception as e:
        processing_flag_blob.upload_from_string(
            json.dumps(
                {
                    "status": "error",
                    "error": str(e),
                    "updated_at": datetime.now().isoformat(),
                }
            )
        )
        raise


async def batch_delete_blobs(
    context: OpExecutionContext, bucket: storage.Bucket, blob_names: List[str]
):
    """
    Asynchronous batch delete for blobs

    Args:
        context (OpExecutionContext): The Dagster operation context
        bucket: GCS bucket
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

            for name in names:
                bucket.blob(name).delete()

        delete_tasks.append(delete_batch(batch))

    if delete_tasks:
        await asyncio.gather(*delete_tasks)
    else:
        context.log.info("No delete tasks created, all batches were empty")


CHUNKED_STATE_JOB_CONFIG = {
    "dagster-k8s/config": {
        "merge_behavior": "SHALLOW",
        "container_config": {
            "resources": {
                "requests": {
                    "cpu": "500m",
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


async def cleanup_incomplete_processes(
    context: OpExecutionContext,
    bucket_name: str,
    prefix: str = "dlt_chunked_state",
    max_age_hours: int = 24,
    clean_completed: bool = True,
    completed_max_age_hours: int = 12,
    client: Optional[storage.Client] = None,
):
    """
    Cleanup function to handle incomplete processes and optionally clean up completed processes.

    Args:
        context (OpExecutionContext): The Dagster operation context
        bucket_name (str): The GCS bucket name
        prefix (str): The GCS prefix
        max_age_hours (int): The maximum age of processing flags to cleanup for incomplete processes
        clean_completed (bool): Whether to also clean up completed processes
        completed_max_age_hours (int): The maximum age for completed processes to clean up
        client (storage.Client): Optional storage client
    """

    if client is None:
        client = storage.Client()

    bucket = client.get_bucket(bucket_name)

    context.log.info(
        f"Scanning for processing flags in bucket '{bucket_name}' with prefix '{prefix}'"
    )
    blobs = list(bucket.list_blobs(prefix=prefix))
    processing_flags = [
        blob for blob in blobs if blob.name.endswith("processing_flag.json")
    ]

    context.log.info(f"Found {len(processing_flags)} processing flag files")
    if not processing_flags:
        context.log.info("No processing flags found, nothing to clean up")
        return

    incomplete_count = 0
    incomplete_young_count = 0
    completed_count = 0
    completed_young_count = 0
    already_cleaned_count = 0
    error_count = 0
    cleanup_tasks = []

    for flag_blob in processing_flags:
        try:
            flag_data = json.loads(flag_blob.download_as_string())
            resource_name = flag_blob.name.split("/")[-2]

            status = flag_data.get("status", "unknown")
            context.log.info(f"Processing resource: {resource_name}, Status: {status}")

            if status == "cleaned":
                context.log.info(
                    f"Resource {resource_name} was already cleaned up on {flag_data.get('cleaned_at', 'unknown date')}"
                )
                already_cleaned_count += 1
                continue

            updated_at = datetime.fromisoformat(
                flag_data.get("updated_at", flag_data.get("started_at"))
            )
            age_hours = (datetime.now() - updated_at).total_seconds() / 3600
            context.log.info(f"Resource {resource_name} age: {age_hours:.1f} hours")

            if status not in ["completed", "cleaned"]:
                if age_hours > max_age_hours:
                    context.log.info(
                        f"Cleaning up incomplete process: {resource_name}"
                        f" (age: {age_hours:.1f} hours, status: {status})"
                    )

                    resource_prefix = "/".join(flag_blob.name.split("/")[:-1])
                    resource_blobs = list(bucket.list_blobs(prefix=resource_prefix))

                    chunk_blobs = [
                        blob for blob in resource_blobs if "chunk." in blob.name
                    ]

                    context.log.info(
                        f"Found {len(chunk_blobs)} chunk files for {resource_name}"
                    )

                    if chunk_blobs:
                        cleanup_tasks.append(
                            batch_delete_blobs(
                                context, bucket, [blob.name for blob in chunk_blobs]
                            )
                        )

                    flag_data["status"] = "cleaned"
                    flag_data["cleaned_at"] = datetime.now().isoformat()
                    flag_blob.upload_from_string(json.dumps(flag_data))
                    incomplete_count += 1
                else:
                    context.log.info(
                        f"Incomplete process {resource_name} is too young to clean up"
                        f" (age: {age_hours:.1f} hours < threshold: {max_age_hours} hours)"
                    )
                    incomplete_young_count += 1

            elif clean_completed and status == "completed":
                if age_hours > completed_max_age_hours:
                    context.log.info(
                        f"Cleaning up completed process: {resource_name}"
                        f" (age: {age_hours:.1f} hours)"
                    )

                    processed_chunks = flag_data.get("processed_chunks", [])
                    context.log.info(
                        f"Found {len(processed_chunks)} processed chunks in flag file"
                    )

                    if processed_chunks:
                        resource_prefix = "/".join(flag_blob.name.split("/")[:-1])
                        chunk_blob_names = [
                            f"{resource_prefix}/chunk.{chunk_id}.json"
                            for chunk_id in processed_chunks
                        ]

                        context.log.info(
                            f"Scheduling deletion of {len(chunk_blob_names)} processed chunks for {resource_name}"
                        )

                        cleanup_tasks.append(
                            batch_delete_blobs(context, bucket, chunk_blob_names)
                        )
                    else:
                        context.log.info(
                            f"No processed chunks found for {resource_name}, nothing to delete"
                        )

                    flag_data["status"] = "cleaned"
                    flag_data["cleaned_at"] = datetime.now().isoformat()
                    flag_blob.upload_from_string(json.dumps(flag_data))
                    completed_count += 1
                else:
                    context.log.info(
                        f"Completed process {resource_name} is too young to clean up"
                        f" (age: {age_hours:.1f} hours < threshold: {completed_max_age_hours} hours)"
                    )
                    completed_young_count += 1
            elif not clean_completed and status == "completed":
                context.log.info(
                    f"Skipping completed process {resource_name} as clean_completed=False"
                )

        except Exception as e:
            context.log.error(f"Error processing flag {flag_blob.name}: {e}")
            error_count += 1

    context.log.info(
        "Cleanup summary before execution:"
        f"\n  - Incomplete processes to clean: {incomplete_count}"
        f"\n  - Incomplete processes too young: {incomplete_young_count}"
        f"\n  - Completed processes to clean: {completed_count}"
        f"\n  - Completed processes too young: {completed_young_count}"
        f"\n  - Already cleaned processes: {already_cleaned_count}"
        f"\n  - Errors encountered: {error_count}"
        f"\n  - Total cleanup tasks: {len(cleanup_tasks)}"
    )

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
    clean_completed: bool = True,
    completed_max_age_hours: int = 12,
    enable: bool = True,
):
    """
    Sets up a sensor and job to clean up incomplete and completed chunked state processes.

    Args:
        gcs_bucket_name (str): GCS bucket name
        gcs_prefix (str): GCS prefix for chunked data
        max_age_hours (int): Maximum age in hours for incomplete processes
        clean_completed (bool): Whether to also clean up completed processes
        completed_max_age_hours (int): The maximum age for completed processes to clean up
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
            f"\n  - Max age for incomplete processes: {max_age_hours} hours"
            f"\n  - Clean completed processes: {clean_completed}"
            f"\n  - Max age for completed processes: {completed_max_age_hours} hours"
        )

        await cleanup_incomplete_processes(
            context=context,
            bucket_name=gcs_bucket_name,
            prefix=gcs_prefix,
            max_age_hours=max_age_hours,
            clean_completed=clean_completed,
            completed_max_age_hours=completed_max_age_hours,
        )

        context.log.info("Chunked state cleanup job completed successfully")

    @job(name="chunked_state_cleanup_job")
    def cleanup_job():
        cleanup_op()

    if enable:
        status = DefaultSensorStatus.RUNNING
    else:
        status = DefaultSensorStatus.STOPPED

    @sensor(
        name="chunked_state_cleanup_sensor",
        job=cleanup_job,
        minimum_interval_seconds=60 * 60 * 6,
        default_status=status,
    )
    def cleanup_sensor(context: SensorEvaluationContext):
        """
        Sensor that periodically triggers the job to clean up chunked state processes.
        This includes both incomplete processes and completed processes based on configuration.
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
