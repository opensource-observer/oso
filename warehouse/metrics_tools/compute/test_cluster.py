import asyncio

import pytest
from dask.distributed import Client
from metrics_tools.compute.cluster import (
    ClusterFactory,
    ClusterManager,
    ClusterProxy,
    ClusterStatus,
)


class FakeClient(Client):
    def __init__(self):
        pass

    def close(self, *args, **kwargs):
        pass

    def register_worker_plugin(self, *args, **kwargs):
        pass


class FakeClusterProxy(ClusterProxy):
    def __init__(self, min_size: int, max_size: int):
        self.min_size = min_size
        self.max_size = max_size

    async def client(self) -> Client:
        return await FakeClient()

    async def status(self):
        return ClusterStatus(
            status="running",
            is_ready=True,
            dashboard_url="",
            workers=1,
        )

    async def stop(self):
        return

    @property
    def dashboard_link(self):
        return "http://fake-dashboard.com"

    @property
    def workers(self):
        return 1


class FakeClusterFactory(ClusterFactory):
    async def create_cluster(self, min_size: int, max_size: int):
        return FakeClusterProxy(min_size, max_size)


@pytest.mark.asyncio
async def test_cluster_manager_reports_ready():
    cluster_manager = ClusterManager.with_dummy_metrics_plugin(FakeClusterFactory())

    ready_future = cluster_manager.wait_for_ready()

    await cluster_manager.start_cluster(1, 1)

    try:
        await asyncio.wait_for(ready_future, timeout=1)
    except asyncio.TimeoutError:
        pytest.fail("Cluster never reported ready")
