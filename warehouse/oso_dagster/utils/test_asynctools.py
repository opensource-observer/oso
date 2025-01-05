from contextlib import asynccontextmanager

import pytest
from oso_dagster.utils.asynctools import multiple_async_contexts


@asynccontextmanager
async def fake_context_manager(ret_val: str):
    yield ret_val


@pytest.mark.asyncio
async def test_multiple_async_contexts():
    async with multiple_async_contexts(
        t1=fake_context_manager("t1"),
        t2=fake_context_manager("t2"),
    ) as context_vars:
        assert context_vars["t1"] == "t1"
        assert context_vars["t2"] == "t2"
