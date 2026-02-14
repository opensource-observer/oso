from unittest.mock import MagicMock

from oso_core.instrumentation.container import MetricsContainer
from oso_core.resources import ResourcesRegistry
from scheduler.config import CommonSettings
from scheduler.mq.concurrency.inmem import InMemoryConcurrencyLockStore
from scheduler.testing.resources.oso_client import FakeOSOClient


def base_testing_resources() -> ResourcesRegistry:
    resources = ResourcesRegistry()

    metrics = MetricsContainer()

    common_settings = CommonSettings(
        oso_api_url="",
        gcp_project_id="",
    )

    resources.add_singleton("concurrency_lock_store", InMemoryConcurrencyLockStore())

    resources.add_singleton("common_settings", common_settings)

    resources.add_singleton("metrics", metrics)

    resources.add_singleton("posthog_client", MagicMock())

    oso_client = FakeOSOClient()

    resources.add_singleton("oso_client", oso_client)
    return resources
