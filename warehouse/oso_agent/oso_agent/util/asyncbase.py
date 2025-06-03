import nest_asyncio

_NEST_ASYNC_IS_LOADED = False

def setup_nest_asyncio():
    global _NEST_ASYNC_IS_LOADED
    if not _NEST_ASYNC_IS_LOADED:
        try:
            nest_asyncio.apply()
            _NEST_ASYNC_IS_LOADED = True
        except ValueError:
            pass

setup_nest_asyncio()