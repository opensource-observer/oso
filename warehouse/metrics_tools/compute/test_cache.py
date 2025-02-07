import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from metrics_tools.compute.cache import CacheExportManager, FakeExportAdapter
from metrics_tools.compute.types import (
    ColumnsDefinition,
    ExportReference,
    ExportType,
    TableReference,
)


@pytest.mark.asyncio
async def test_cache_export_manager():
    adapter_mock = AsyncMock(FakeExportAdapter)
    adapter_mock.export_table.return_value = ExportReference(
        table=TableReference(table_name="test"),
        type=ExportType.GCS,
        columns=ColumnsDefinition(columns=[]),
        payload={},
    )
    cache = await CacheExportManager.setup(adapter_mock)
    execution_time = datetime.now()

    export_table_0 = await asyncio.wait_for(
        cache.resolve_export_references(["table1", "table2"], execution_time), timeout=1
    )

    assert export_table_0.keys() == {"table1", "table2"}

    # Attempt to export tables again but this should be mostly cache hits except
    # for table3
    export_table_1 = await asyncio.wait_for(
        cache.resolve_export_references(
            ["table1", "table2", "table1", "table3"], execution_time
        ),
        timeout=1,
    )
    assert export_table_1.keys() == {"table1", "table2", "table3"}

    assert adapter_mock.export_table.call_count == 3


class TestException(Exception):
    pass


@pytest.mark.asyncio
async def test_cache_export_manager_fails():
    adapter_mock = AsyncMock(FakeExportAdapter)
    adapter_mock.export_table = AsyncMock(side_effect=TestException("test"))
    cache = await CacheExportManager.setup(adapter_mock)
    execution_time = datetime.now()

    failed = False
    try:
        await asyncio.wait_for(
            cache.resolve_export_references(["table1"], execution_time), timeout=5
        )
    except TestException as e:
        assert str(e) == "test"
        failed = True
    await cache.stop()
    assert failed, "Expected exception to be raised"
