import logging
from typing import Any, Dict, Generator

import dlt
import requests
from dagster import AssetExecutionContext, ResourceParam
from dlt.destinations.adapters import bigquery_adapter
from dlt.sources.helpers.requests import Session
from dlt.sources.rest_api.typing import RESTAPIConfig
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory
from oso_dagster.factories.rest import create_rest_factory_asset

logger = logging.getLogger(__name__)

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
        },
    },
}

# REST API configuration for projects
config: RESTAPIConfig = {
    "client": {
        "base_url": "https://l2beat.com/api",
    },
    "resource_defaults": {
        "write_disposition": "replace",
    },
    "resources": [
        {
            "name": "projects",
            "endpoint": {
                "path": "scaling/summary",
                "data_selector": "$.data.projects",
            },
        }
    ],
}

# REST API assets for projects
dlt_assets = create_rest_factory_asset(
    config=config,
)

l2beat_projects_assets = dlt_assets(
    key_prefix="l2beat",
    name="projects",
)


def get_l2beat_activity_data(
    context: AssetExecutionContext,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch L2Beat activity data for all projects and yield individual activity records.

    Args:
        context (AssetExecutionContext): The execution context

    Yields:
        Dict[str, Any]: Individual activity records
    """
    session = Session(timeout=300)

    # First, get the list of all projects to extract their slugs
    projects_url = "https://l2beat.com/api/scaling/summary"

    try:
        context.log.info("Fetching L2Beat projects to get slugs")
        response = session.get(projects_url)
        response.raise_for_status()
        projects_data = response.json()

        projects = projects_data.get("data", {}).get("projects", {})
        slugs = list(projects.keys())

        context.log.info(f"Found {len(slugs)} projects to fetch activity data for")

        # Fetch activity data for each slug
        for slug in slugs:
            try:
                activity_url = (
                    f"https://l2beat.com/api/scaling/activity/{slug}?range=7d"
                )
                context.log.info(f"Fetching activity data for {slug}")

                response = session.get(activity_url)
                response.raise_for_status()
                activity_data = response.json()

                if not activity_data.get("success"):
                    context.log.warning(
                        f"Failed to fetch activity data for {slug}: API returned success=false"
                    )
                    continue

                chart_data = activity_data.get("data", {}).get("chart", {})
                types = chart_data.get("types", [])
                data_points = chart_data.get("data", [])

                # Process each data point
                for data_point in data_points:
                    if len(data_point) == len(types):
                        activity_record = {
                            "project_slug": slug,
                            **dict(zip(types, data_point)),
                        }
                        yield activity_record
                    else:
                        context.log.warning(
                            f"Data point length mismatch for {slug}: expected {len(types)}, got {len(data_point)}"
                        )

            except requests.exceptions.RequestException as e:
                context.log.error(f"Failed to fetch activity data for {slug}: {e}")
                continue
            except Exception as e:
                context.log.error(f"Error processing activity data for {slug}: {e}")
                continue

    except requests.exceptions.RequestException as e:
        context.log.error(f"Failed to fetch projects from L2Beat API: {e}")
        raise
    except Exception as e:
        context.log.error(f"Error processing L2Beat activity data: {e}")
        raise


@dlt_factory(
    key_prefix="l2beat",
    name="activity",
    op_tags={
        "dagster/concurrency_key": "l2beat_activity",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def l2beat_activity_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Create and register a Dagster asset that materializes L2Beat activity data.

    Args:
        context (AssetExecutionContext): The execution context of the asset.
        global_config (DagsterConfig): Global configuration parameters.

    Yields:
        Generator: A generator that yields L2Beat activity records.
    """
    resource = dlt.resource(
        get_l2beat_activity_data(context),
        name="activity",
        primary_key=["project_slug", "timestamp"],
        write_disposition="replace",
    )

    if global_config.gcp_bigquery_enabled:
        bigquery_adapter(
            resource,
            cluster=["project_slug", "timestamp"],
        )

    yield resource
