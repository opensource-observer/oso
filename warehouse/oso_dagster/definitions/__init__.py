import logging
import typing as t

from dagster import ConfigurableIOManagerFactory, Definitions
from dagster_dlt import DagsterDltResource
from dagster_gcp import BigQueryResource, GCSResource
from dagster_k8s import k8s_job_executor
from dagster_sqlmesh import SQLMeshContextConfig, SQLMeshResource
from dlt.common.destination import Destination
from oso_core.logging import setup_module_logging
from oso_core.logging.decorators import time_function
from oso_dagster.cbt.cbt import CBTResource
from oso_dagster.definitions.common import load_definitions_with_asset_factories
from oso_dagster.definitions.resources import run_with_default_resources
from oso_dagster.factories.common import ResourcesContext
from oso_dagster.resources import (
    BigQueryDataTransferResource,
    ClickhouseResource,
    DuckDBResource,
    K8sResource,
    PrefixedSQLMeshTranslator,
    SQLMeshExporter,
    TrinoResource,
)
from oso_dagster.resources.bq import BigQueryImporterResource
from oso_dagster.resources.clickhouse import ClickhouseImporterResource
from oso_dagster.resources.duckdb import DuckDBExporterResource, DuckDBImporterResource
from oso_dagster.resources.storage import TimeOrderedStorageResource
from oso_dagster.resources.trino import TrinoExporterResource
from oso_dagster.utils.alerts import AlertManager
from oso_dagster.utils.secrets import SecretResolver

from ..config import DagsterConfig

logger = logging.getLogger(__name__)


@time_function(logger)
def load_definitions(
    resources: ResourcesContext,
    global_config: DagsterConfig,
    cbt: CBTResource,
    gcs: GCSResource,
    bigquery: BigQueryResource,
    bigquery_datatransfer: BigQueryDataTransferResource,
    clickhouse: ClickhouseResource,
    io_manager: ConfigurableIOManagerFactory,
    duckdb: DuckDBResource,
    secret_resolver: SecretResolver,
    dlt_staging_destination: Destination,
    dlt_warehouse_destination: Destination,
    dlt: DagsterDltResource,
    alert_manager: AlertManager,
    sqlmesh_config: SQLMeshContextConfig,
    sqlmesh_infra_config: t.Dict[str, str],
    sqlmesh: SQLMeshResource,
    k8s: K8sResource,
    trino: TrinoResource,
    sqlmesh_translator: PrefixedSQLMeshTranslator,
    sqlmesh_exporters: t.List[SQLMeshExporter],
    trino_exporter: TrinoExporterResource,
    clickhouse_importer: ClickhouseImporterResource,
    bigquery_importer: BigQueryImporterResource,
    duckdb_exporter: DuckDBExporterResource,
    duckdb_importer: DuckDBImporterResource,
    time_ordered_storage: TimeOrderedStorageResource,
) -> Definitions:
    from .. import assets
    from ..factories import load_all_assets_from_package
    from ..factories.alerts import setup_alert_sensors
    from ..schedules import get_partitioned_schedules, schedules
    from ..utils import setup_chunked_state_cleanup_sensor

    setup_module_logging("oso_dagster")

    asset_factories = load_all_assets_from_package(assets, resources)
    alerts = setup_alert_sensors(
        global_config.alerts_base_url,
        alert_manager,
        False,
    )

    asset_factories = asset_factories + alerts

    chunked_state_cleanup_sensor = setup_chunked_state_cleanup_sensor(
        global_config.gcs_bucket,
    )

    asset_factories = asset_factories + chunked_state_cleanup_sensor

    all_schedules = schedules + get_partitioned_schedules(asset_factories)

    resources_dict = {
        "gcs": gcs,
        "cbt": cbt,
        "bigquery": bigquery,
        "bigquery_datatransfer": bigquery_datatransfer,
        "clickhouse": clickhouse,
        "io_manager": io_manager,
        "dlt": dlt,
        "secrets": secret_resolver,
        "dlt_staging_destination": dlt_staging_destination,
        "dlt_warehouse_destination": dlt_warehouse_destination,
        "project_id": global_config.project_id,
        "alert_manager": alert_manager,
        "sqlmesh_config": sqlmesh_config,
        "sqlmesh_infra_config": sqlmesh_infra_config,
        "sqlmesh": SQLMeshResource(config=sqlmesh_config),
        "k8s": k8s,
        "trino": trino,
        "global_config": global_config,
        "sqlmesh_translator": sqlmesh_translator,
        "sqlmesh_exporters": sqlmesh_exporters,
        "trino_exporter": trino_exporter,
        "clickhouse_importer": clickhouse_importer,
        "bigquery_importer": bigquery_importer,
        "duckdb_exporter": duckdb_exporter,
        "duckdb_importer": duckdb_importer,
        "time_ordered_storage": time_ordered_storage,
    }

    extra_kwargs = {}
    if global_config.enable_k8s_executor:
        extra_kwargs["executor"] = k8s_job_executor.configured(
            {
                "max_concurrent": 10,
            }
        )

    return load_definitions_with_asset_factories(
        asset_factories,
        schedules=all_schedules,
        resources=resources_dict,
        **extra_kwargs,
    )


defs = run_with_default_resources(load_definitions)
