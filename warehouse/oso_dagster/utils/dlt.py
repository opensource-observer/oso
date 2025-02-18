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
    ParamSpec,
    TypeVar,
)

from dagster import AssetExecutionContext
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
        fn: Callable[K, Generator[Callable[..., Coroutine[Any, Any, R]], None, None]]
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

            tasks: List[Coroutine[Any, Any, R]] = [
                task() for task in fn(*args, **kwargs)
            ]
            batches_list = list(batched(tasks, config.chunk_size))

            for batch_group in batched(batches_list, config.parallel_batches):
                log.info(
                    f"DLTParallelize: Executing {len(batch_group)} batch(es) in parallel"
                )
                group_coroutines = [coro for batch in batch_group for coro in batch]

                results = [
                    await future for future in asyncio.as_completed(group_coroutines)
                ]

                for result in results:
                    yield result

                log.info(
                    f"DLTParallelize: Waiting for {config.wait_interval} seconds ..."
                )

                chunk_update_fn = kwargs.get("_chunk_resource_update")
                if chunk_update_fn and isinstance(chunk_update_fn, Callable):
                    chunk_update_fn(results)
                else:
                    log.warning("DLTParallelize: chunk_update_fn function not found")

                await asyncio.sleep(config.wait_interval)

            retrieve_failed_fn = kwargs.get("_chunk_retrieve_failed")
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
        to_string_fn (Callable): Function that converts a single data unit
            to a string representation. For Pydantic models, this can be the model's
            `model_dump_json` method.
        gcs_bucket_name (str): Google Cloud Storage bucket name.
        gcs_prefix (str): Google Cloud Storage prefix for chunked data. Defaults
            to "dlt_chunked_state".
        max_manifest_age (int): Maximum age of the manifest file in seconds. If the
            manifest file is older than this value, the manifest will be reset. This
            means that the `fetch_data_fn` will be called again, re-fetching all the
            data and starting from scratch. Defaults to 24 hours.
        context (AssetExecutionContext): Dagster context object.
    """

    def __init__(
        self,
        fetch_data_fn: Callable[[], List[T]],
        resource: DltResource,
        to_string_fn: Callable[..., str],
        gcs_bucket_name: str,
        gcs_prefix: str = "dlt_chunked_state",
        max_manifest_age: int = 60 * 60 * 24,
        context: AssetExecutionContext | None = None,
    ):
        self.fetch_data_fn = fetch_data_fn
        self.resource = resource
        self.to_string_fn = to_string_fn
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
    client = storage.Client()
    bucket = client.get_bucket(config.gcs_bucket_name)
    state_blob = bucket.blob(f"{config.gcs_prefix}/{config.resource.name}/state.json")

    log = config.context.log if config.context else logger

    log.info(f"ChunkedResource: Checking state in {state_blob.name}")

    def resource_update(elements: List[List]):
        count = len(elements)
        current_manifest = state_blob.download_as_string()
        current_data = json.loads(current_manifest)

        current_data["pending_data"] = current_data["pending_data"][count:]
        current_data["updated_at"] = datetime.now().isoformat()

        log.info(
            f"ChunkedResource: Updating state with {len(current_data['pending_data'])} pending entries"
        )

        state_blob.upload_from_string(json.dumps(current_data))

        if not current_data["pending_data"]:
            log.info("ChunkedResource: No more pending data, deleting state")
            state_blob.delete()

        stringified_elems = [
            config.to_string_fn(elem) for sublist in elements for elem in sublist
        ]

        new_blob = bucket.blob(
            f"{config.gcs_prefix}/{config.resource.name}/chunk.{uuid.uuid4()}.json"
        )

        new_blob.upload_from_string(json.dumps(stringified_elems))

        log.info(f"ChunkedResource: Uploaded {count} elements to {new_blob.name}")

    def retrieve_failed(yield_elems: bool):
        blobs = bucket.list_blobs(
            prefix=f"{config.gcs_prefix}/{config.resource.name}/chunk."
        )

        if yield_elems:
            for blob in blobs:
                if blob.name.endswith(".json"):
                    log.info(f"ChunkedResource: Retrieving chunk {blob.name}")
                    yield json.loads(blob.download_as_string())

        blobs = bucket.list_blobs(prefix=f"{config.gcs_prefix}/{config.resource.name}")

        for blob in blobs:
            if blob.name.endswith(".json"):
                log.info(f"ChunkedResource: Deleting {blob.name}")
                blob.delete()

    kwargs["_chunk_retrieve_failed"] = partial(retrieve_failed, False)

    try:
        if not state_blob.exists():
            raise NotFound("State file does not exist")

        manifest = state_blob.download_as_string()
        manifest_data = json.loads(manifest)

        log.info("ChunkedResource: Found existing state manifest")
        kwargs["_chunk_retrieve_failed"] = partial(retrieve_failed, True)

        if (
            datetime.now() - datetime.fromisoformat(manifest_data["updated_at"])
            or datetime.now() - datetime.fromisoformat(manifest_data["created_at"])
        ).total_seconds() > config.max_manifest_age:
            log.info("ChunkedResource: State manifest is too old, resetting")
            manifest_data = None
            kwargs["_chunk_retrieve_failed"] = partial(retrieve_failed, False)

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
