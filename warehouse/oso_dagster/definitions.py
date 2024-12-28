import os

from dagster import Definitions
from dagster_dbt import DbtCliResource
from dagster_embedded_elt.dlt import DagsterDltResource
from dagster_gcp import BigQueryResource, GCSResource
from dagster_k8s import k8s_job_executor
from dagster_sqlmesh import SQLMeshContextConfig, SQLMeshResource
from dotenv import load_dotenv
from oso_dagster.utils.dbt import support_home_dir_profiles

from . import assets, constants
from .cbt import CBTResource
from .factories import load_all_assets_from_package
from .factories.alerts import setup_alert_sensor
from .resources import (
    BigQueryDataTransferResource,
    ClickhouseResource,
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

load_dotenv()


def load_definitions():
    project_id = constants.project_id
    secret_resolver = LocalSecretResolver(prefix="DAGSTER")
    if not constants.use_local_secrets:
        secret_resolver = GCPSecretResolver.connect_with_default_creds(
            project_id, constants.gcp_secrets_prefix
        )

    # A dlt destination for gcs staging to bigquery
    dlt_staging_destination = load_dlt_staging()

    dlt_warehouse_destination = load_dlt_warehouse_destination()

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

    sqlmesh_config = SQLMeshContextConfig(
        path=constants.sqlmesh_dir, gateway=constants.sqlmesh_gateway
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
        staging_bucket=constants.staging_bucket,
        dlt_staging_destination=dlt_staging_destination,
        dlt_warehouse_destination=dlt_warehouse_destination,
        secrets=secret_resolver,
        sqlmesh_config=sqlmesh_config,
        sqlmesh_infra_config=sqlmesh_infra_config,
    )

    asset_factories = load_all_assets_from_package(assets, early_resources)

    # io_manager = PolarsBigQueryIOManager(project=project_id)
    io_manager = load_io_manager()

    # Setup an alert sensor
    alert_manager = LogAlertManager()
    if constants.discord_webhook_url:
        alert_manager = CanvasDiscordWebhookAlertManager(constants.discord_webhook_url)

    alerts = setup_alert_sensor(
        "alerts",
        constants.dagster_alerts_base_url,
        alert_manager,
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
    }
    for target in constants.main_dbt_manifests:
        resources[f"{target}_dbt"] = DbtCliResource(
            project_dir=os.fspath(constants.main_dbt_project_dir),
            target=target,
            profiles_dir=support_home_dir_profiles(),
        )

    extra_kwargs = {}
    if constants.enable_k8s_executor:
        extra_kwargs["executor"] = k8s_job_executor

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
