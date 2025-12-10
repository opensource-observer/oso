import typing as t

from oso_core.resources import ResourcesContext, ResourcesRegistry, resource_factory
from oso_dagster.resources.duckdb import DuckDBResource
from oso_dagster.resources.heartbeat import HeartBeatResource
from oso_dagster.resources.kube import K8sApiResource, K8sResource
from oso_dagster.resources.trino import (
    TrinoK8sResource,
    TrinoRemoteResource,
    TrinoResource,
)
from oso_dagster.resources.udm_engine_adapter import (
    DuckdbEngineAdapterResource,
    TrinoEngineAdapterResource,
    UserDefinedModelEngineAdapterResource,
)
from oso_dagster.resources.udm_state import (
    FakeUserDefinedModelResource,
    UserDefinedModelStateResource,
)
from scheduler.evaluator import UserDefinedModelEvaluator
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.mq.handlers.data_model import DataModelRunRequestHandler
from scheduler.mq.pubsub import GCPPubSubMessageQueueService
from scheduler.testing.client import FakeUDMClient
from scheduler.types import (
    GenericMessageQueueService,
    MessageQueueHandlerRegistry,
    UserDefinedModelStateClient,
)

if t.TYPE_CHECKING:
    from scheduler.config import CommonSettings


@resource_factory("message_queue_service")
def message_queue_service_factory(
    resources: ResourcesContext,
    common_settings: "CommonSettings",
) -> GenericMessageQueueService:
    """Factory function to create a message queue service resource."""
    registry = MessageQueueHandlerRegistry()
    registry.register(DataModelRunRequestHandler())

    return GCPPubSubMessageQueueService(
        project_id=common_settings.gcp_project_id,
        resources=resources,
        registry=registry,
        emulator_enabled=common_settings.emulator_enabled,
    )


@resource_factory("udm_engine_adapter")
def udm_engine_adapter_factory(
    resources: ResourcesContext, common_settings: "CommonSettings"
) -> UserDefinedModelEngineAdapterResource:
    """Factory function to create a UDM engine adapter resource."""

    if common_settings.trino_enabled:
        trino: TrinoResource = resources.resolve("trino")
        return TrinoEngineAdapterResource(
            trino=trino,
            http_scheme="https",
        )
    else:
        duckdb: DuckDBResource = resources.resolve("duckdb")
        return DuckdbEngineAdapterResource(
            duckdb=duckdb,
        )


@resource_factory("udm_client")
def udm_client_factory() -> UserDefinedModelStateClient:
    """Factory function to create a UDM client resource."""
    return FakeUDMClient()


@resource_factory("udm_state")
def udm_state_factory() -> UserDefinedModelStateResource:
    """Factory function to create a UDM state resource."""

    # Use a fake UDM state resource for now as this is a stub until we implement
    # all the APIs properly.
    return FakeUserDefinedModelResource()


@resource_factory("trino")
def trino_resource_factory(
    common_settings: "CommonSettings",
    k8s: K8sResource | K8sApiResource,
    heartbeat: HeartBeatResource,
) -> TrinoResource:
    if not common_settings.k8s_enabled:
        return TrinoRemoteResource()
    return TrinoK8sResource(
        k8s=k8s,
        namespace=common_settings.trino_k8s_namespace,
        service_name=common_settings.trino_k8s_service_name,
        coordinator_deployment_name=common_settings.trino_k8s_coordinator_deployment_name,
        worker_deployment_name=common_settings.trino_k8s_worker_deployment_name,
        use_port_forward=common_settings.k8s_use_port_forward,
        heartbeat=heartbeat,
    )


@resource_factory("duckdb")
def duckdb_resource_factory(
    common_settings: "CommonSettings",
) -> DuckDBResource:
    """Factory function to create a DuckDB resource."""
    return DuckDBResource(database_path=common_settings.local_duckdb_path)


@resource_factory("k8s")
def k8s_resource_factory(
    common_settings: "CommonSettings",
) -> K8sResource | K8sApiResource:
    if not common_settings.k8s_enabled:
        return K8sResource()
    return K8sApiResource()


@resource_factory("evaluator")
def scheduler_evaluator_factory(
    udm_client: UserDefinedModelStateClient,
) -> UserDefinedModelEvaluator:
    """Factory function to create a UDM evaluator."""
    return UserDefinedModelEvaluator(udm_client)


@resource_factory("oso_client")
def oso_client_factory(common_settings: "CommonSettings") -> OSOClient:
    """Factory function to create an OSO client."""
    # For now, return None as a placeholder.
    return OSOClient(url=common_settings.oso_api_url)


def default_resource_registry(common_settings: "CommonSettings") -> ResourcesRegistry:
    registry = ResourcesRegistry()
    registry.add_singleton("common_settings", common_settings)

    registry.add(udm_engine_adapter_factory)
    registry.add(udm_state_factory)
    registry.add(trino_resource_factory)
    registry.add(duckdb_resource_factory)
    registry.add(k8s_resource_factory)
    registry.add(message_queue_service_factory)
    registry.add(scheduler_evaluator_factory)
    registry.add(udm_client_factory)

    return registry
