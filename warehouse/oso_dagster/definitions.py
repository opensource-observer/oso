import os

from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource
from dagster_gcp import BigQueryResource, GCSResource

from .constants import main_dbt_project_dir, main_dbt_manifests
from .schedules import schedules
from .cbt import CBTResource
from .factories import load_assets_factories_from_modules
from . import assets

from dotenv import load_dotenv

load_dotenv()


def load_definitions():
    bigquery = BigQueryResource(project=os.environ.get("GOOGLE_PROJECT_ID"))
    gcs = GCSResource(project=os.environ.get("GOOGLE_PROJECT_ID"))
    cbt = CBTResource(
        bigquery=bigquery,
        search_paths=[os.path.join(os.path.dirname(__file__), "models")],
    )

    asset_factories = load_assets_factories_from_modules([assets])
    asset_defs = load_assets_from_modules([assets])

    resources = {
        "gcs": gcs,
        "cbt": cbt,
        "bigquery": bigquery,
    }
    for target in main_dbt_manifests:
        resources[f"{target}_dbt"] = DbtCliResource(
            project_dir=os.fspath(main_dbt_project_dir), target=target
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
