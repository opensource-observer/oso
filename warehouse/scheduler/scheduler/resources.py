import typing as t

import structlog
from dlt.sources.credentials import AwsCredentials, FileSystemCredentials
from oso_core.instrumentation import MetricsContainer
from oso_core.resources import ResourcesContext, ResourcesRegistry, resource_factory
from oso_dagster.resources import GCSFileResource
from oso_dagster.resources.duckdb import DuckDBResource
from oso_dagster.resources.heartbeat import (
    FilebasedHeartBeatResource,
    HeartBeatResource,
    RedisHeartBeatResource,
)
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
from scheduler.dlt_destination import (
    DLTDestinationResource,
    DuckDBDLTDestinationResource,
    TrinoDLTDestinationResource,
)
from scheduler.evaluator import UserDefinedModelEvaluator
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.materialization.duckdb import DuckdbMaterializationStrategy
from scheduler.materialization.trino import TrinoMaterializationStrategy
from scheduler.mq.handlers.data_ingestion import DataIngestionRunRequestHandler
from scheduler.mq.handlers.data_model import DataModelRunRequestHandler
from scheduler.mq.handlers.publish_notebook import PublishNotebookRunRequestHandler
from scheduler.mq.handlers.query import QueryRunRequestHandler
from scheduler.mq.handlers.static_model import StaticModelRunRequestHandler
from scheduler.mq.pubsub import GCPPubSubMessageQueueService
from scheduler.testing.client import FakeUDMClient
from scheduler.types import (
    GenericMessageQueueService,
    MaterializationStrategy,
    MessageHandlerRegistry,
    UserDefinedModelStateClient,
)

if t.TYPE_CHECKING:
    from scheduler.config import CommonSettings

logger = structlog.get_logger(__name__)


@resource_factory("message_queue_service")
def message_queue_service_factory(
    resources: ResourcesContext,
    common_settings: "CommonSettings",
    message_handler_registry: MessageHandlerRegistry,
    metrics: MetricsContainer,
) -> GenericMessageQueueService:
    """Factory function to create a message queue service resource."""
    return GCPPubSubMessageQueueService(
        project_id=common_settings.gcp_project_id,
        resources=resources,
        registry=message_handler_registry,
        emulator_enabled=common_settings.emulator_enabled,
        metrics=metrics,
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


@resource_factory("heartbeat")
def heartbeat_factory(common_settings: "CommonSettings") -> HeartBeatResource:
    """Factory function to create a heartbeat resource."""
    if common_settings.k8s_enabled or common_settings.redis_host:
        assert common_settings.redis_host is not None, (
            "Redis host must be set for Redis heartbeat."
        )
        logger.info("Using RedisHeartBeatResource for heartbeat.")
        return RedisHeartBeatResource(
            host=common_settings.redis_host,
            port=common_settings.redis_port,
        )
    else:
        logger.info("Using FilebasedHeartBeatResource for heartbeat.")
        return FilebasedHeartBeatResource(
            directory=common_settings.local_heartbeat_path,
        )


@resource_factory("consumer_trino")
def consumer_trino_resource_factory(
    common_settings: "CommonSettings",
    k8s: K8sResource | K8sApiResource,
    heartbeat: HeartBeatResource,
) -> TrinoResource:
    if not common_settings.k8s_enabled:
        return TrinoRemoteResource()
    return TrinoK8sResource(
        k8s=k8s,
        namespace=common_settings.consumer_trino_k8s_namespace,
        service_name=common_settings.consumer_trino_k8s_service_name,
        coordinator_deployment_name=common_settings.consumer_trino_k8s_coordinator_deployment_name,
        worker_deployment_name=common_settings.consumer_trino_k8s_worker_deployment_name,
        use_port_forward=common_settings.k8s_use_port_forward,
        heartbeat_name="consumer_trino",
        heartbeat=heartbeat,
        # Consumer configuration
        catalog="iceberg",
        connection_schema="oso",
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
    if not common_settings.oso_system_api_key:
        raise ValueError(
            "OSO system API key is not set. Set SCHEDULER_OSO_SYSTEM_API_KEY."
        )

    return OSOClient(
        url=common_settings.oso_api_url,
        headers={"x-system-credentials": common_settings.oso_system_api_key},
    )


@resource_factory("message_handler_registry")
def message_handler_registry_factory() -> MessageHandlerRegistry:
    """Factory function to create a message handler registry."""
    registry = MessageHandlerRegistry()
    registry.register(DataModelRunRequestHandler())
    registry.register(DataIngestionRunRequestHandler())
    registry.register(QueryRunRequestHandler())
    registry.register(StaticModelRunRequestHandler())
    registry.register(PublishNotebookRunRequestHandler())
    return registry


@resource_factory("gcs")
def gcs_factory(common_settings: "CommonSettings") -> GCSFileResource:
    """Factory function to create a GCS file resource."""
    return GCSFileResource(gcs_project=common_settings.gcp_project_id)


@resource_factory("materialization_strategy")
def materialization_strategy_factory(
    common_settings: "CommonSettings",
) -> MaterializationStrategy:
    """Factory function to create a materialization strategy."""
    if common_settings.trino_enabled:
        return TrinoMaterializationStrategy(
            base_catalog_name=common_settings.warehouse_shared_catalog_name
        )
    else:
        return DuckdbMaterializationStrategy(
            base_catalog_name=common_settings.warehouse_shared_catalog_name
        )


@resource_factory("dlt_destination")
def dlt_destination_factory(
    resources: ResourcesContext,
    common_settings: "CommonSettings",
) -> DLTDestinationResource:
    """Factory function to create a DLT destination resource.

    Returns a configured DLT destination based on the common_settings.
    Uses Trino if trino_enabled is True, otherwise uses DuckDB.
    """
    if common_settings.trino_enabled:
        trino: TrinoResource = resources.resolve("trino")
        return TrinoDLTDestinationResource(
            trino=trino, catalog=common_settings.warehouse_shared_catalog_name
        )
    else:
        return DuckDBDLTDestinationResource(
            database_path=common_settings.local_duckdb_path
        )


@resource_factory("upload_filesystem_credentials")
def upload_filesystem_credentials_factory(
    common_settings: "CommonSettings",
) -> FileSystemCredentials | None:
    """Factory function to create DLT filesystem credentials resource."""

    if (
        common_settings.upload_filesystem_access_key_id
        and common_settings.upload_filesystem_secret_access_key
    ):
        return AwsCredentials(
            aws_access_key_id=common_settings.upload_filesystem_access_key_id,
            aws_secret_access_key=common_settings.upload_filesystem_secret_access_key,
            endpoint_url=common_settings.upload_filesystem_endpoint_url,
            region_name="auto",
        )
    return None


@resource_factory("metrics")
def metrics_factory() -> MetricsContainer:
    """Factory function to create a metrics container resource."""
    metrics = MetricsContainer()
    return metrics


def default_resource_registry(common_settings: "CommonSettings") -> ResourcesRegistry:
    registry = ResourcesRegistry()
    registry.add_singleton("common_settings", common_settings)

    registry.add(udm_engine_adapter_factory)
    registry.add(trino_resource_factory)
    registry.add(consumer_trino_resource_factory)
    registry.add(duckdb_resource_factory)
    registry.add(k8s_resource_factory)
    registry.add(message_queue_service_factory)
    registry.add(scheduler_evaluator_factory)
    registry.add(udm_client_factory)
    registry.add(oso_client_factory)
    registry.add(message_handler_registry_factory)
    registry.add(heartbeat_factory)
    registry.add(materialization_strategy_factory)
    registry.add(dlt_destination_factory)
    registry.add(gcs_factory)
    registry.add(upload_filesystem_credentials_factory)
    registry.add(metrics_factory)

    return registry
