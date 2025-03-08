import logging
import os

from dagster import Definitions
from dagster_dbt import DbtCliResource
from dagster_embedded_elt.dlt import DagsterDltResource
from dagster_gcp import BigQueryResource, GCSResource
from dagster_k8s import k8s_job_executor
from dagster_sqlmesh import SQLMeshContextConfig, SQLMeshResource
from dotenv import find_dotenv, load_dotenv
from metrics_tools.utils.logging import setup_module_logging
from oso_dagster.resources.bq import BigQueryImporterResource
from oso_dagster.resources.clickhouse import ClickhouseImporterResource
from oso_dagster.resources.duckdb import (
    DuckDBExporterResource,
    DuckDBImporterResource,
    DuckDBResource,
)
from oso_dagster.resources.storage import (
    GCSTimeOrderedStorageResource,
    TimeOrderedStorageResource,
)
from oso_dagster.resources.trino import TrinoExporterResource
from oso_dagster.utils.dbt import support_home_dir_profiles

from . import assets
from .cbt import CBTResource
from .config import DagsterConfig
from .factories import load_all_assets_from_package
from .factories.alerts import setup_alert_sensors
from .resources import (
    BigQueryDataTransferResource,
    ClickhouseResource,
    K8sApiResource,
    K8sResource,
    MCSK8sResource,
    MCSRemoteResource,
    PrefixedSQLMeshTranslator,
    Trino2BigQuerySQLMeshExporter,
    Trino2ClickhouseSQLMeshExporter,
    TrinoK8sResource,
    TrinoRemoteResource,
    load_dlt_staging,
    load_dlt_warehouse_destination,
    load_io_manager,
)
from .schedules import get_partitioned_schedules, schedules
from .utils import (
    CanvasDiscordWebhookAlertManager,
    GCPSecretResolver,
    LocalSecretResolver,
    LogAlertManager,
)

logger = logging.getLogger(__name__)

if os.environ.get("ENV") == "local":
    load_dotenv(find_dotenv(".env.local"))
elif os.environ.get("ENV") == "production":
    load_dotenv(find_dotenv(".env.production"))
load_dotenv()


def load_definitions():
    setup_module_logging("oso_dagster")
    # Load the configuration for the project
    global_config = DagsterConfig()  # type: ignore
    global_config.initialize()

    logger.debug(f"Loaded global_config={global_config}")

    project_id = global_config.project_id
    secret_resolver = LocalSecretResolver(prefix="DAGSTER")
    if not global_config.use_local_secrets:
        secret_resolver = GCPSecretResolver.connect_with_default_creds(
            project_id, global_config.gcp_secrets_prefix
        )

    # A dlt destination for gcs staging to bigquery
    dlt_staging_destination = load_dlt_staging(global_config)

    dlt_warehouse_destination = load_dlt_warehouse_destination(global_config)

    dlt = DagsterDltResource()

    bigquery = BigQueryResource(project=project_id)
    bigquery_datatransfer = BigQueryDataTransferResource(
        project=os.environ.get("GOOGLE_PROJECT_ID")
    )

    clickhouse = ClickhouseResource(
        secrets=secret_resolver, secret_group_name="clickhouse"
    )

    gcs = GCSResource(project=project_id)
    cbt = CBTResource(
        bigquery=bigquery,
        search_paths=[os.path.join(os.path.dirname(__file__), "models")],
    )

    sqlmesh_catalog = global_config.sqlmesh_catalog
    sqlmesh_schema = global_config.sqlmesh_schema
    sqlmesh_bq_export_dataset_id = global_config.sqlmesh_bq_export_dataset_id

    sqlmesh_translator = PrefixedSQLMeshTranslator("sqlmesh")

    sqlmesh_config = SQLMeshContextConfig(
        path=global_config.sqlmesh_dir, gateway=global_config.sqlmesh_gateway
    )

    sqlmesh_exporter = [
        Trino2ClickhouseSQLMeshExporter(
            ["clickhouse_metrics"],
            destination_catalog="clickhouse",
            destination_schema="default",
            source_catalog=sqlmesh_catalog,
            source_schema=sqlmesh_schema,
        ),
        Trino2BigQuerySQLMeshExporter(
            ["bigquery_metrics"],
            project_id=project_id,
            dataset_id=sqlmesh_bq_export_dataset_id,
            source_catalog=sqlmesh_catalog,
            source_schema=sqlmesh_schema,
        ),
    ]
    # If we aren't running in k8s, we need to use a dummy k8s resource that will
    # error if we attempt to use it
    if not global_config.enable_k8s:
        logger.info("Loading fake k8s resources")
        k8s = K8sResource()
        trino = TrinoRemoteResource()
        mcs = MCSRemoteResource()
        time_ordered_storage = TimeOrderedStorageResource()

    else:
        logger.info("Loading k8s resources")
        k8s = K8sApiResource()
        trino = TrinoK8sResource(
            k8s=k8s,
            namespace=global_config.trino_k8s_namespace,
            service_name=global_config.trino_k8s_service_name,
            coordinator_deployment_name=global_config.trino_k8s_coordinator_deployment_name,
            worker_deployment_name=global_config.trino_k8s_worker_deployment_name,
            use_port_forward=global_config.k8s_use_port_forward,
        )
        mcs = MCSK8sResource(
            k8s=k8s,
            namespace=global_config.mcs_k8s_namespace,
            service_name=global_config.mcs_k8s_service_name,
            deployment_name=global_config.mcs_k8s_deployment_name,
            use_port_forward=global_config.k8s_use_port_forward,
        )
        sqlmesh_exporter = [
            Trino2ClickhouseSQLMeshExporter(
                ["clickhouse_metrics"],
                destination_catalog="clickhouse",
                destination_schema="default",
                source_catalog=sqlmesh_catalog,
                source_schema=sqlmesh_schema,
            ),
            Trino2BigQuerySQLMeshExporter(
                ["bigquery_metrics"],
                project_id=project_id,
                dataset_id=sqlmesh_bq_export_dataset_id,
                source_catalog=sqlmesh_catalog,
                source_schema=sqlmesh_schema,
            ),
        ]
        time_ordered_storage = GCSTimeOrderedStorageResource(
            bucket_name=global_config.gcs_bucket
        )

    trino_exporter = TrinoExporterResource(
        trino=trino, time_ordered_storage=time_ordered_storage
    )
    clickhouse_importer = ClickhouseImporterResource(clickhouse=clickhouse)
    bigquery_importer = BigQueryImporterResource(bigquery=bigquery)
    duckdb_exporter = DuckDBExporterResource(
        duckdb=DuckDBResource(
            database_path=global_config.local_duckdb_path,
        ),
        time_ordered_storage=time_ordered_storage,
    )
    duckdb_importer = DuckDBImporterResource(
        duckdb=DuckDBResource(
            database_path=global_config.local_duckdb_path,
        )
    )

    sqlmesh_infra_config = {
        "environment": "prod",
        "mcs_deployment_name": "production-mcs",
        "mcs_deployment_namespace": "production-mcs",
        "trino_deployment_namespace": "production-trino",
        "trino_service_name": "production-trino-trino",
        "trino_coordinator_deployment_name": "production-trino-trino-coordinator",
        "trino_worker_deployment_name": "production-trino-trino-worker",
    }

    early_resources = dict(
        project_id=project_id,
        staging_bucket=global_config.staging_bucket_url,
        dlt_staging_destination=dlt_staging_destination,
        dlt_warehouse_destination=dlt_warehouse_destination,
        secrets=secret_resolver,
        sqlmesh_config=sqlmesh_config,
        sqlmesh_infra_config=sqlmesh_infra_config,
        global_config=global_config,
        sqlmesh_translator=sqlmesh_translator,
        sqlmesh_exporters=sqlmesh_exporter,
        trino_exporter=trino_exporter,
        clickhouse_importer=clickhouse_importer,
        bigquery_importer=bigquery_importer,
        duckdb_exporter=duckdb_exporter,
        duckdb_importer=duckdb_importer,
        time_ordered_storage=time_ordered_storage,
    )

    asset_factories = load_all_assets_from_package(assets, early_resources)

    # io_manager = PolarsBigQueryIOManager(project=project_id)
    io_manager = load_io_manager(global_config)

    # Setup an alert sensor
    alert_manager = LogAlertManager()
    if global_config.discord_webhook_url:
        alert_manager = CanvasDiscordWebhookAlertManager(
            global_config.discord_webhook_url
        )

    alerts = setup_alert_sensors(
        global_config.alerts_base_url,
        alert_manager,
        False,
    )

    asset_factories = asset_factories + alerts

    all_schedules = schedules + get_partitioned_schedules(asset_factories)

    # Each of the dbt environments needs to be setup as a resource to be used in
    # the dbt assets
    resources = {
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
        "project_id": project_id,
        "alert_manager": alert_manager,
        "sqlmesh_config": sqlmesh_config,
        "sqlmesh_infra_config": sqlmesh_infra_config,
        "sqlmesh": SQLMeshResource(config=sqlmesh_config),
        "k8s": k8s,
        "trino": trino,
        "mcs": mcs,
        "global_config": global_config,
        "sqlmesh_translator": sqlmesh_translator,
        "sqlmesh_exporters": sqlmesh_exporter,
        "trino_exporter": trino_exporter,
        "clickhouse_importer": clickhouse_importer,
        "bigquery_importer": bigquery_importer,
        "duckdb_exporter": duckdb_exporter,
        "duckdb_importer": duckdb_importer,
        "time_ordered_storage": time_ordered_storage,
    }
    for target in global_config.dbt_manifests:
        resources[f"{target}_dbt"] = DbtCliResource(
            project_dir=os.fspath(global_config.main_dbt_project_dir),
            target=target,
            profiles_dir=support_home_dir_profiles(),
        )

    extra_kwargs = {}
    if global_config.enable_k8s_executor:
        extra_kwargs["executor"] = k8s_job_executor.configured(
            {
                "max_concurrent": 10,
            }
        )

    return Definitions(
        assets=asset_factories.assets,
        schedules=all_schedules,
        jobs=asset_factories.jobs,
        asset_checks=asset_factories.checks,
        sensors=asset_factories.sensors,
        resources=resources,
        **extra_kwargs,
    )


defs = load_definitions()
