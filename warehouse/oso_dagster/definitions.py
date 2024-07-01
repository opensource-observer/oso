import os

from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource
from dagster_gcp import BigQueryResource, GCSResource
from dagster_polars import PolarsBigQueryIOManager

from . import constants
from .schedules import schedules
from .cbt import CBTResource
from .factories import load_assets_factories_from_modules
from .resources import BigQueryDataTransferResource
from . import assets

from dagster_embedded_elt.dlt import DagsterDltResource

from dotenv import load_dotenv
load_dotenv()

def load_definitions():
    dlt = DagsterDltResource()
    bigquery = BigQueryResource(project=os.environ.get("GOOGLE_PROJECT_ID"))
    bigquery_datatransfer = BigQueryDataTransferResource(project=os.environ.get("GOOGLE_PROJECT_ID"))
    gcs = GCSResource(project=os.environ.get("GOOGLE_PROJECT_ID"))
    cbt = CBTResource(
        bigquery=bigquery,
        search_paths=[os.path.join(os.path.dirname(__file__), "models")],
    )

    asset_factories = load_assets_factories_from_modules([assets])
    asset_defs = load_assets_from_modules([assets])

    io_manager = PolarsBigQueryIOManager(project=constants.project_id)

    # Each of the dbt environments needs to be setup as a resource to be used in
    # the dbt assets
    resources = {
        "gcs": gcs,
        "cbt": cbt,
        "bigquery": bigquery,
        "bigquery_datatransfer": bigquery_datatransfer,
        "io_manager": io_manager,
        "dlt": dlt,
    }
    for target in constants.main_dbt_manifests:
        resources[f"{target}_dbt"] = DbtCliResource(
            project_dir=os.fspath(constants.main_dbt_project_dir), target=target
        )

    return Definitions(
        assets=list(asset_defs) + asset_factories.assets,
        schedules=schedules,
        jobs=asset_factories.jobs,
        asset_checks=asset_factories.checks,
        sensors=asset_factories.sensors,
        resources=resources,
    )


defs = load_definitions()
