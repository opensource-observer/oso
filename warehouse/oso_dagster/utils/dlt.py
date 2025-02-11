import asyncio
from dataclasses import dataclass
from itertools import batched
from typing import Any, Callable, Coroutine, Generator, List, ParamSpec, TypeVar

from dagster import AssetExecutionContext

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
                    if context:
                        context.log.info(
                            f"DLTParallelize: Executing {len(batch_group)} batch(es) in parallel"
                        )

                    group_coroutines = [coro for batch in batch_group for coro in batch]

                    for future in asyncio.as_completed(group_coroutines):
                        res = await future
                        results.append(res)

                    if context:
                        context.log.info(
                            f"DLTParallelize: Waiting for {config.wait_interval} seconds ..."
                        )
                    await asyncio.sleep(config.wait_interval)

                return results

            yield from asyncio.run(process_batches())

        return _wrapper

    return _decorator
