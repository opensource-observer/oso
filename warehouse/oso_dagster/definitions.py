import os

from dagster import Definitions
from dagster_dbt import DbtCliResource
from dagster_gcp import BigQueryResource, GCSResource
from dagster_polars import PolarsBigQueryIOManager
from dlt.destinations import filesystem

from . import constants
from .schedules import schedules
from .cbt import CBTResource
from .factories import load_all_assets_from_package
from .utils import (
    LocalSecretResolver,
    GCPSecretResolver,
    LogAlertManager,
    DiscordWebhookAlertManager,
)
from .resources import BigQueryDataTransferResource
from . import assets
from .factories.alerts import setup_alert_sensor

from dagster_embedded_elt.dlt import DagsterDltResource

from dotenv import load_dotenv

load_dotenv()


def load_definitions():
    project_id = constants.project_id
    secret_resolver = LocalSecretResolver("dagster")
    if not constants.use_local_secrets:
        secret_resolver = GCPSecretResolver.connect_with_default_creds(
            project_id, constants.gcp_secrets_prefix
        )

    # A dlt destination for gcs staging to bigquery
    assert constants.staging_bucket_url is not None
    dlt_gcs_staging = filesystem(bucket_url=constants.staging_bucket_url)

    dlt = DagsterDltResource()
    bigquery = BigQueryResource(project=project_id)
    bigquery_datatransfer = BigQueryDataTransferResource(
        project=os.environ.get("GOOGLE_PROJECT_ID")
    )
    gcs = GCSResource(project=project_id)
    cbt = CBTResource(
        bigquery=bigquery,
        search_paths=[os.path.join(os.path.dirname(__file__), "models")],
    )

    early_resources = dict(
        project_id=project_id, dlt_gcs_staging=dlt_gcs_staging, secrets=secret_resolver
    )

    asset_factories = load_all_assets_from_package(assets, early_resources)

    io_manager = PolarsBigQueryIOManager(project=project_id)

    # Setup an alert sensor
    alert_manager = LogAlertManager()
    if constants.discord_webhook_url:
        alert_manager = DiscordWebhookAlertManager(constants.discord_webhook_url)
    alerts = setup_alert_sensor(
        "alerts",
        constants.dagster_alerts_base_url,
        alert_manager,
    )

    asset_factories = asset_factories + alerts

    # Each of the dbt environments needs to be setup as a resource to be used in
    # the dbt assets
    resources = {
        "gcs": gcs,
        "cbt": cbt,
        "bigquery": bigquery,
        "bigquery_datatransfer": bigquery_datatransfer,
        "io_manager": io_manager,
        "dlt": dlt,
        "secrets": secret_resolver,
        "dlt_gcs_staging": dlt_gcs_staging,
        "project_id": project_id,
    }
    for target in constants.main_dbt_manifests:
        resources[f"{target}_dbt"] = DbtCliResource(
            project_dir=os.fspath(constants.main_dbt_project_dir), target=target
        )

    return Definitions(
        assets=asset_factories.assets,
        schedules=schedules,
        jobs=asset_factories.jobs,
        asset_checks=asset_factories.checks,
        sensors=asset_factories.sensors,
        resources=resources,
    )


defs = load_definitions()
