import asyncio
import typing as t


def safe_async_run[T](coro: t.Coroutine[t.Any, t.Any, T]) -> T:
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
