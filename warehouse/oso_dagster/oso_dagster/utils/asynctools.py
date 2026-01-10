import asyncio
import typing as t
from contextlib import asynccontextmanager


def safe_async_run[T](coro: t.Coroutine[t.Any, t.Any, T]) -> T:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)
    return loop.run_until_complete(coro)


@asynccontextmanager
async def multiple_async_contexts(
    **context_managers: t.AsyncContextManager[t.Any],
) -> t.AsyncGenerator[t.Dict[str, t.Any], t.Any]:
    """Runs multiple async context managers in parallel

    This ensures that all context managers are entered and yields everything in
    a single dictionary of all the context vars. The dictionary's keys are the
    names passed into the keyword arguments of this function

    Example:

        .. code-block:: python::

            async with multiple_async_contexts(
                a=asynccontextmanager_a(),
                b=asynccontextmanager_b(),
            ) as context:
                context_for_a = context["a"]
                context_for_b = context["b"]

    """

    assert context_managers, "At least one context manager must be provided"

    async def enter(name: str, cm: t.AsyncContextManager[t.Any]) -> t.Any:
        context = await cm.__aenter__()
        return (name, context)

    context_entrances: t.List[t.Awaitable[t.Any]] = [
        enter(name, cm) for name, cm in context_managers.items()
    ]
    results = await asyncio.gather(*context_entrances)
    context_dict = {name: context for name, context in results}
    try:
        yield context_dict
    except Exception as e:
        context_exits = [
            cm.__aexit__(type(e), e, e.__traceback__)
            for cm in context_managers.values()
        ]
        await asyncio.gather(*context_exits)
        raise e
    else:
        context_exits = [
            cm.__aexit__(None, None, None) for cm in context_managers.values()
        ]
        await asyncio.gather(*context_exits)
