import typing as t

import structlog
from dagster import ConfigurableIOManagerFactory
from dagster_dlt import DagsterDltResource
from dagster_gcp import BigQueryResource, GCSResource
from dagster_sqlmesh import SQLMeshContextConfig, SQLMeshResource
from dlt.common.destination import Destination
from oso_core.logging.decorators import time_function
from oso_dagster.cbt.cbt import CBTResource
from oso_dagster.factories import resource_factory
from oso_dagster.factories.common import ResourcesRegistry
from oso_dagster.resources import (
    BigQueryDataTransferResource,
    ClickhouseResource,
    DuckDBResource,
    K8sApiResource,
    K8sResource,
    PrefixedSQLMeshTranslator,
    SQLMeshExporter,
    Trino2BigQuerySQLMeshExporter,
    Trino2ClickhouseSQLMeshExporter,
    TrinoK8sResource,
    TrinoRemoteResource,
    TrinoResource,
    load_dlt_staging,
    load_dlt_warehouse_destination,
    load_io_manager,
)
from oso_dagster.resources.bq import BigQueryImporterResource
from oso_dagster.resources.clickhouse import ClickhouseImporterResource
from oso_dagster.resources.duckdb import DuckDBExporterResource
from oso_dagster.resources.storage import (
    GCSTimeOrderedStorageResource,
    TimeOrderedStorageResource,
)
from oso_dagster.resources.trino import TrinoExporterResource
from oso_dagster.utils.alerts import (
    AlertManager,
    CanvasDiscordWebhookAlertManager,
    LogAlertManager,
)
from oso_dagster.utils.secrets import SecretResolver

from ..config import DagsterConfig
from ..utils import GCPSecretResolver, LocalSecretResolver

logger = structlog.get_logger(__name__)


@resource_factory("global_config")
@time_function(logger)
def global_config_factory() -> DagsterConfig:
    """Factory function to create a DagsterConfig instance."""
    return DagsterConfig()


@resource_factory("secrets")
@time_function(logger)
def secrets_factory(
    global_config: DagsterConfig,
) -> LocalSecretResolver | GCPSecretResolver:
    """Factory function to create a secret resolver based on the configuration."""
    if global_config.use_local_secrets:
        return LocalSecretResolver(prefix="DAGSTER")
    return GCPSecretResolver.connect_with_default_creds(
        global_config.project_id, global_config.gcp_secrets_prefix
    )


@resource_factory("bigquery")
@time_function(logger)
def bigquery_resource_factory(global_config: DagsterConfig) -> BigQueryResource:
    """Factory function to create a BigQuery resource."""
    return BigQueryResource(project=global_config.project_id)


@resource_factory("bigquery_datatransfer")
@time_function(logger)
def bigquery_datatransfer_resource_factory(
    global_config: DagsterConfig,
) -> BigQueryDataTransferResource:
    """Factory function to create a BigQuery Data Transfer resource."""
    return BigQueryDataTransferResource(project=global_config.project_id)


@resource_factory("clickhouse")
@time_function(logger)
def clickhouse_resource_factory(
    global_config: DagsterConfig,
    secrets: LocalSecretResolver | GCPSecretResolver,
) -> ClickhouseResource:
    """Factory function to create a Clickhouse resource."""
    return ClickhouseResource(
        secrets=secrets,
        secret_group_name=global_config.clickhouse_secret_group_name,
    )


@resource_factory("gcs")
@time_function(logger)
def gcs_resource_factory(global_config: DagsterConfig) -> GCSResource:
    return GCSResource(project=global_config.project_id)


@resource_factory("sqlmesh_translator")
@time_function(logger)
def sqlmesh_translator_factory():
    return PrefixedSQLMeshTranslator("sqlmesh")


@resource_factory("sqlmesh_config")
@time_function(logger)
def sqlmesh_config_factory(global_config: DagsterConfig) -> SQLMeshContextConfig:
    return SQLMeshContextConfig(
        path=global_config.sqlmesh_dir,
        gateway=global_config.sqlmesh_gateway,
    )


@resource_factory("k8s")
@time_function(logger)
def k8s_resource_factory(global_config: DagsterConfig) -> K8sResource | K8sApiResource:
    if not global_config.enable_k8s:
        return K8sResource()
    return K8sApiResource()


@resource_factory("trino")
@time_function(logger)
def trino_resource_factory(
    global_config: DagsterConfig, k8s: K8sResource | K8sApiResource
) -> TrinoResource:
    if not global_config.enable_k8s:
        return TrinoRemoteResource()
    return TrinoK8sResource(
        k8s=k8s,
        namespace=global_config.trino_k8s_namespace,
        service_name=global_config.trino_k8s_service_name,
        coordinator_deployment_name=global_config.trino_k8s_coordinator_deployment_name,
        worker_deployment_name=global_config.trino_k8s_worker_deployment_name,
        use_port_forward=global_config.k8s_use_port_forward,
    )


@resource_factory("sqlmesh")
def sqlmesh_resource_factory(
    sqlmesh_config: SQLMeshContextConfig,
) -> SQLMeshResource:
    """Factory function to create a SQLMesh resource."""
    return SQLMeshResource(
        config=sqlmesh_config,
    )


@resource_factory("sqlmesh_exporters")
@time_function(logger)
def sqlmesh_exporter_factory(global_config: DagsterConfig) -> t.List[SQLMeshExporter]:
    return [
        Trino2ClickhouseSQLMeshExporter(
            ["clickhouse_metrics"],
            destination_catalog="clickhouse",
            destination_schema="default",
            source_catalog=global_config.sqlmesh_catalog,
            source_schema=global_config.sqlmesh_schema,
        ),
        Trino2BigQuerySQLMeshExporter(
            ["bigquery_metrics"],
            project_id=global_config.project_id,
            dataset_id=global_config.sqlmesh_bq_export_dataset_id,
            source_catalog=global_config.sqlmesh_catalog,
            source_schema=global_config.sqlmesh_schema,
        ),
    ]


# dlt staging destination
@resource_factory("dlt_staging_destination")
@time_function(logger)
def dlt_staging_destination_factory(
    global_config: DagsterConfig,
) -> Destination:
    """Factory function to create a DLT staging destination."""
    return load_dlt_staging(global_config)


@resource_factory("dlt_warehouse_destination")
@time_function(logger)
def dlt_warehouse_destination_factory(
    global_config: DagsterConfig,
) -> Destination:
    """Factory function to create a DLT warehouse destination."""
    return load_dlt_warehouse_destination(global_config)


@resource_factory("dlt")
@time_function(logger)
def dlt_resource_factory() -> DagsterDltResource:
    return DagsterDltResource()


@resource_factory("cbt")
@time_function(logger)
def cbt_resource_factory(
    global_config: DagsterConfig, bigquery: BigQueryResource
) -> CBTResource:
    return CBTResource(
        bigquery=bigquery,
        search_paths=global_config.cbt_search_paths,
    )


@resource_factory("trino_exporter")
@time_function(logger)
def trino_exporter_factory(
    time_ordered_storage: TimeOrderedStorageResource,
    trino: TrinoResource,
):
    return TrinoExporterResource(
        trino=trino,
        time_ordered_storage=time_ordered_storage,
    )


# clickhouse importer
@resource_factory("clickhouse_importer")
@time_function(logger)
def clickhouse_importer_factory(
    global_config: DagsterConfig,
    clickhouse: ClickhouseResource,
    secrets: SecretResolver,
) -> ClickhouseImporterResource:
    """Factory function to create a Clickhouse importer."""
    return ClickhouseImporterResource(
        clickhouse=clickhouse,
        secrets=secrets,
        secret_group_name=global_config.clickhouse_importer_secret_group_name,
    )


# bigquery importer
@resource_factory("bigquery_importer")
@time_function(logger)
def bigquery_importer_factory(
    bigquery: BigQueryResource,
) -> BigQueryImporterResource:
    """Factory function to create a BigQuery importer."""
    return BigQueryImporterResource(bigquery=bigquery)


@resource_factory("duckdb")
@time_function(logger)
def duckdb_resource_factory(
    global_config: DagsterConfig,
) -> DuckDBResource:
    """Factory function to create a DuckDB resource."""
    return DuckDBResource(database_path=global_config.local_duckdb_path)


# duckdb exporter
@resource_factory("duckdb_exporter")
@time_function(logger)
def duckdb_exporter_factory(
    time_ordered_storage: TimeOrderedStorageResource,
    duckdb: DuckDBResource,
) -> DuckDBExporterResource:
    """Factory function to create a DuckDB exporter."""
    return DuckDBExporterResource(
        time_ordered_storage=time_ordered_storage, duckdb=duckdb
    )


# duckdb importer
@resource_factory("duckdb_importer")
@time_function(logger)
def duckdb_importer_factory(
    time_ordered_storage: TimeOrderedStorageResource,
    duckdb: DuckDBResource,
) -> DuckDBExporterResource:
    """Factory function to create a DuckDB importer."""
    return DuckDBExporterResource(
        time_ordered_storage=time_ordered_storage, duckdb=duckdb
    )


# sqlmesh infra config
@resource_factory("sqlmesh_infra_config")
@time_function(logger)
def sqlmesh_infra_config_factory() -> t.Dict[str, str]:
    """Factory function to create SQLMesh infrastructure configuration."""

    return {
        "dev_environment": "dev",
        "environment": "prod",
        "mcs_deployment_name": "production-mcs",
        "mcs_deployment_namespace": "production-mcs",
        "trino_deployment_namespace": "production-trino",
        "trino_service_name": "production-trino-trino",
        "trino_coordinator_deployment_name": "production-trino-trino-coordinator",
        "trino_worker_deployment_name": "production-trino-trino-worker",
    }


@resource_factory("io_manager")
@time_function(logger)
def io_manager_factory(
    global_config: DagsterConfig,
) -> ConfigurableIOManagerFactory:
    """Factory function to create an IO manager."""
    return load_io_manager(global_config)


@resource_factory("alert_manager")
@time_function(logger)
def alert_manager_factory(global_config: DagsterConfig) -> AlertManager:
    """Factory function to create an alert manager."""
    # Placeholder for alert manager resource
    # This can be replaced with an actual implementation
    if global_config.discord_webhook_url:
        return CanvasDiscordWebhookAlertManager(global_config.discord_webhook_url)
    return LogAlertManager()


@resource_factory("time_ordered_storage")
@time_function(logger)
def time_ordered_storage_factory(
    global_config: DagsterConfig,
) -> TimeOrderedStorageResource:
    if not global_config.enable_k8s:
        return TimeOrderedStorageResource()
    return GCSTimeOrderedStorageResource(
        bucket_name=global_config.gcs_bucket,
    )


def default_resource_registry():
    """By default we can configure all resource factories as the resource
    resolution is lazy."""

    registry = ResourcesRegistry()

    registry.add(global_config_factory)
    registry.add(secrets_factory)
    registry.add(bigquery_resource_factory)
    registry.add(bigquery_datatransfer_resource_factory)
    registry.add(clickhouse_resource_factory)
    registry.add(gcs_resource_factory)
    registry.add(sqlmesh_resource_factory)
    registry.add(sqlmesh_translator_factory)
    registry.add(sqlmesh_config_factory)
    registry.add(k8s_resource_factory)
    registry.add(trino_resource_factory)
    registry.add(sqlmesh_exporter_factory)
    registry.add(dlt_staging_destination_factory)
    registry.add(dlt_warehouse_destination_factory)
    registry.add(dlt_resource_factory)
    registry.add(cbt_resource_factory)
    registry.add(trino_exporter_factory)
    registry.add(clickhouse_importer_factory)
    registry.add(bigquery_importer_factory)
    registry.add(duckdb_resource_factory)
    registry.add(duckdb_exporter_factory)
    registry.add(duckdb_importer_factory)
    registry.add(sqlmesh_infra_config_factory)
    registry.add(io_manager_factory)
    registry.add(alert_manager_factory)
    registry.add(time_ordered_storage_factory)

    return registry
