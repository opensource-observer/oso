import asyncio
import typing as t


def safe_async_run[T](coro: t.Coroutine[t.Any, t.Any, T]) -> T:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)
    return loop.run_until_complete(coro)
