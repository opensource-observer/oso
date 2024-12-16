import asyncio
from datetime import datetime

import pytest
from metrics_tools.compute.cache import CacheExportManager, FakeExportAdapter
from metrics_tools.compute.cluster import ClusterManager, LocalClusterFactory
from metrics_tools.compute.result import DummyImportAdapter
from metrics_tools.compute.service import MetricsCalculationService
from metrics_tools.compute.types import (
    ClusterStartRequest,
    ColumnsDefinition,
    ExportReference,
    ExportType,
    JobSubmitRequest,
    QueryJobStatus,
)
from metrics_tools.definition import PeerMetricDependencyRef


@pytest.mark.asyncio
async def test_metrics_calculation_service():
    service = MetricsCalculationService.setup(
        "someid",
        "bucket",
        "result_path_prefix",
        ClusterManager.with_dummy_metrics_plugin(LocalClusterFactory()),
        await CacheExportManager.setup(FakeExportAdapter()),
        DummyImportAdapter(),
    )
    await service.start_cluster(ClusterStartRequest(min_size=1, max_size=1))
    await service.add_existing_exported_table_references(
        {
            "source.table123": ExportReference(
                table_name="export_table123",
                type=ExportType.GCS,
                columns=ColumnsDefinition(
                    columns=[("col1", "INT"), ("col2", "TEXT")], dialect="duckdb"
                ),
                payload={"gcs_path": "gs://bucket/result_path_prefix/export_table123"},
            ),
        }
    )
    response = await service.submit_job(
        JobSubmitRequest(
            query_str="SELECT * FROM ref.table123",
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 3),
            dialect="duckdb",
            batch_size=1,
            columns=[("col1", "int"), ("col2", "string")],
            ref=PeerMetricDependencyRef(
                name="test",
                entity_type="artifact",
                window=30,
                unit="day",
            ),
            execution_time=datetime.now(),
            locals={},
            dependent_tables_map={"source.table123": "source.table123"},
        )
    )

    async def wait_for_job_to_complete():
        status = await service.get_job_status(response.job_id)
        while status.status in [QueryJobStatus.PENDING, QueryJobStatus.RUNNING]:
            status = await service.get_job_status(response.job_id)
            await asyncio.sleep(1)

    await asyncio.wait_for(asyncio.create_task(wait_for_job_to_complete()), timeout=60)
    status = await service.get_job_status(response.job_id)
    assert status.status == QueryJobStatus.COMPLETED

    await service.close()
