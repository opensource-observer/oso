import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import cmp_to_key
from itertools import batched
from typing import (
    Any,
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
    Decorator for parallelizing a synchronous generator function that yields callables.

    The decorated function is expected to be synchronous and yield callables that, when called,
    return a coroutine (i.e. of type Callable[..., Coroutine[Any, Any, R]]). The decorator converts
    these callables into coroutine objects, batches them using the specified configuration,
    runs them concurrently using asyncio, and yields their results synchronously.

    Args:
        config (ParallelizeConfig): Configuration object
    """

    def _decorator(
        fn: Callable[K, Generator[Callable[..., Coroutine[Any, Any, R]], None, None]]
    ) -> Callable[K, Generator[R, None, None]]:
        """
        Decorator function that wraps the original synchronous generator function.

        Args:
            fn (Callable): The original function that yields callables returning coroutine objects.
        """

        def _wrapper(*args: K.args, **kwargs: K.kwargs) -> Generator[R, None, None]:
            """
            Synchronous wrapper that processes coroutine tasks in parallel and yields results.

            Args:
                *args: Positional arguments forwarded to the original function.
                **kwargs: Keyword arguments forwarded to the original function.
            """

            context = next(
                (arg for arg in args if isinstance(arg, AssetExecutionContext)), None
            )

            log = context.log if context else logger

            async def process_batches() -> List[R]:
                """
                Asynchronously collects and processes coroutine tasks in batches.

                This function:
                  - Calls the original function to get a generator of callables.
                  - Converts each callable into a coroutine object.
                  - Splits the list of coroutines into batches based on `chunk_size`.
                  - Processes these batches concurrently in groups based on `parallel_batches`.
                  - Waits asynchronously between batch groups as defined by `wait_interval`.
                """

                results: List[R] = []
                tasks: List[Coroutine[Any, Any, R]] = [
                    task() for task in fn(*args, **kwargs)
                ]
                batches_list = list(batched(tasks, config.chunk_size))

                for batch_group in batched(batches_list, config.parallel_batches):
                    log.info(
                        f"DLTParallelize: Executing {len(batch_group)} batch(es) in parallel"
                    )

                    group_coroutines = [coro for batch in batch_group for coro in batch]

                    for future in asyncio.as_completed(group_coroutines):
                        res = await future
                        results.append(res)

                    log.info(
                        f"DLTParallelize: Waiting for {config.wait_interval} seconds ..."
                    )

                    await asyncio.sleep(config.wait_interval)

                return results

            yield from asyncio.run(process_batches())

        return _wrapper

    return _decorator


T = TypeVar("T")


class ChunkedResourceConfig(Generic[T]):
    def __init__(
        self,
        fetch_data_fn: Callable[[], List[T]],
        resource: DltResource,
        chunk_size: int,
        gcs_bucket_name: str,
        sort_fn: Callable[[T, T], int],
        gcs_prefix: str = "_chunked_state",
        max_data_age: int = 60 * 60 * 24,
        context: AssetExecutionContext | None = None,
    ):
        self.fetch_data_fn = fetch_data_fn
        self.resource = resource
        self.chunk_size = chunk_size
        self.gcs_bucket_name = gcs_bucket_name
        self.sort_fn = sort_fn
        self.gcs_prefix = gcs_prefix
        self.max_data_age = max_data_age
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

    try:
        manifest = state_blob.download_as_string()
        manifest_data = json.loads(manifest)

        log.info("ChunkedResource: Found existing state manifest")

        if (
            datetime.now() - datetime.fromisoformat(manifest_data["updated_at"])
            or datetime.now() - datetime.fromisoformat(manifest_data["created_at"])
        ).total_seconds() > config.max_data_age:
            log.info("ChunkedResource: State manifest is too old, resetting")
            manifest_data = None

    except (NotFound, json.JSONDecodeError):
        log.info("ChunkedResource: No existing state found, creating new manifest")
        manifest_data = None

    if manifest_data is None:
        log.info("ChunkedResource: Processing input data")
        data = config.fetch_data_fn()

        log.info("ChunkedResource: Sorting and chunking input data")
        sorted_data = sorted(data, key=cmp_to_key(config.sort_fn))
        chunks = [list(batch) for batch in batched(sorted_data, config.chunk_size)]

        log.info(
            f"ChunkedResource: Created {len(chunks)} chunks of size {config.chunk_size}"
        )

        manifest_data = {
            "updated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "processed_chunks": [],
            "pending_chunks": chunks,
        }

        log.info("ChunkedResource: Uploading initial manifest")
        state_blob.upload_from_string(json.dumps(manifest_data))

    pending_chunks = list(manifest_data["pending_chunks"])

    for chunk in pending_chunks:
        log.info(f"ChunkedResource: Processing chunk with {len(chunk)} items")

        try:
            yield config.resource(chunk, *args, **kwargs)

            manifest_data["processed_chunks"].append(chunk)
            manifest_data["pending_chunks"].remove(chunk)
            manifest_data["updated_at"] = datetime.now().isoformat()

            log.info("ChunkedResource: Chunk processed successfully, updating manifest")
            state_blob.upload_from_string(json.dumps(manifest_data))

        except Exception as e:
            log.error(f"ChunkedResource: Failed to process chunk: {e}")
            raise

    if manifest_data["pending_chunks"]:
        log.error("ChunkedResource: Unprocessed chunks remain, exiting")
        raise Exception("ChunkedResource: Unprocessed chunks remain, exiting")

    log.info("ChunkedResource: All chunks processed, exiting")
    state_blob.delete()

    try:
        bucket.delete_blob(f"{config.gcs_prefix}/{config.resource.name}")
    except NotFound:
        pass
