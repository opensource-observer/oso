import logging
import random
import time
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

BASE_URL = "https://l2beat.com/api"
DEFAULT_ACTIVITY_RANGE = "max"
DEFAULT_TIMEOUT = 300
DEFAULT_REQUEST_DELAY = 3.0
DEFAULT_BASE_DELAY = 30.0
DEFAULT_MAX_DELAY = 120.0
DEFAULT_MAX_RETRIES = 3

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
        },
    },
}

config: RESTAPIConfig = {
    "client": {
        "base_url": BASE_URL,
    },
    "resource_defaults": {
        "write_disposition": "replace",
    },
    "resources": [
        {
            "name": "projects",
            "endpoint": {
                "path": "scaling/summary",
                "data_selector": "$.projects",
            },
        }
    ],
}

dlt_assets = create_rest_factory_asset(
    config=config,
)

l2beat_projects_assets = dlt_assets(
    key_prefix="l2beat",
    name="projects",
)


def make_request_with_backoff(
    session: Session,
    url: str,
    context: AssetExecutionContext,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> requests.Response:
    """
    Make a request with exponential backoff retry logic for rate limiting.
    """
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url)

            if response.status_code == 429:
                if attempt < max_retries:
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter

                    context.log.warning(
                        f"Rate limited (429) on attempt {attempt + 1}/{max_retries + 1}. "
                        f"Retrying in {total_delay:.1f} seconds..."
                    )
                    time.sleep(total_delay)
                    continue
                else:
                    context.log.error(
                        f"Rate limited (429) after {max_retries} retries. Giving up."
                    )
                    response.raise_for_status()

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                delay = min(base_delay * (2**attempt), max_delay)
                jitter = random.uniform(0.1, 0.3) * delay
                total_delay = delay + jitter

                context.log.warning(
                    f"Request failed on attempt {attempt + 1}/{max_retries + 1}: {e}. "
                    f"Retrying in {total_delay:.1f} seconds..."
                )
                time.sleep(total_delay)
                continue
            else:
                context.log.error(f"Request failed after {max_retries} retries: {e}")
                raise

    raise requests.exceptions.RequestException("Unexpected end of retry loop")


def get_l2beat_activity_data(
    context: AssetExecutionContext,
    activity_range: str = DEFAULT_ACTIVITY_RANGE,
    timeout: int = DEFAULT_TIMEOUT,
    request_delay: float = DEFAULT_REQUEST_DELAY,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch L2Beat activity data for all projects and yield individual activity records.
    """
    session = Session(timeout=timeout)

    projects_url = f"{BASE_URL}/scaling/summary"

    try:
        context.log.info("Fetching L2Beat projects to get slugs")
        response = session.get(projects_url)
        response.raise_for_status()
        projects_data = response.json()

        projects = projects_data.get("projects", {})

        slugs = list(projects.keys())

        context.log.info(f"Found {len(slugs)} projects to fetch activity data for")

        for i, slug in enumerate(slugs):
            try:
                if i > 0:
                    time.sleep(request_delay)

                activity_url = (
                    f"{BASE_URL}/scaling/activity/{slug}?range={activity_range}"
                )
                context.log.info(
                    f"Fetching activity data for {slug} ({i + 1}/{len(slugs)})"
                )

                response = make_request_with_backoff(
                    session, activity_url, context, base_delay, max_delay, max_retries
                )
                activity_data = response.json()

                if not activity_data.get("success"):
                    context.log.warning(
                        f"Failed to fetch activity data for {slug}: API returned success=false"
                    )
                    continue

                chart_data = activity_data.get("data", {}).get("chart", {})
                types = chart_data.get("types", [])
                data_points = chart_data.get("data", [])

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


def get_l2beat_tvs_data(
    context: AssetExecutionContext,
    tvs_range: str = DEFAULT_ACTIVITY_RANGE,
    timeout: int = DEFAULT_TIMEOUT,
    request_delay: float = DEFAULT_REQUEST_DELAY,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetch L2Beat TVS data for all projects and yield individual TVS records.
    """
    session = Session(timeout=timeout)

    projects_url = f"{BASE_URL}/scaling/summary"

    try:
        context.log.info("Fetching L2Beat projects to get slugs")
        response = session.get(projects_url)
        response.raise_for_status()
        projects_data = response.json()

        projects = projects_data.get("projects", {})

        slugs = list(projects.keys())

        context.log.info(f"Found {len(slugs)} projects to fetch TVS data for")

        for i, slug in enumerate(slugs):
            try:
                if i > 0:
                    time.sleep(request_delay)

                tvs_url = f"{BASE_URL}/scaling/tvs/{slug}?range={tvs_range}"
                context.log.info(f"Fetching TVS data for {slug} ({i + 1}/{len(slugs)})")

                response = make_request_with_backoff(
                    session, tvs_url, context, base_delay, max_delay, max_retries
                )
                tvs_data = response.json()

                if not tvs_data.get("success"):
                    context.log.warning(
                        f"Failed to fetch TVS data for {slug}: API returned success=false"
                    )
                    continue

                chart_data = tvs_data.get("data", {}).get("chart", {})
                types = chart_data.get("types", [])
                data_points = chart_data.get("data", [])

                for data_point in data_points:
                    if len(data_point) == len(types):
                        tvs_record = {
                            "project_slug": slug,
                            **dict(zip(types, data_point)),
                        }
                        yield tvs_record
                    else:
                        context.log.warning(
                            f"Data point length mismatch for {slug}: expected {len(types)}, got {len(data_point)}"
                        )

            except requests.exceptions.RequestException as e:
                context.log.error(f"Failed to fetch TVS data for {slug}: {e}")
                continue
            except Exception as e:
                context.log.error(f"Error processing TVS data for {slug}: {e}")
                continue

    except requests.exceptions.RequestException as e:
        context.log.error(f"Failed to fetch projects from L2Beat API: {e}")
        raise
    except Exception as e:
        context.log.error(f"Error processing L2Beat TVS data: {e}")
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


@dlt_factory(
    key_prefix="l2beat",
    name="tvs",
    op_tags={
        "dagster/concurrency_key": "l2beat_tvs",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def l2beat_tvs_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Create and register a Dagster asset that materializes L2Beat TVS data.
    """
    resource = dlt.resource(
        get_l2beat_tvs_data(context),
        name="tvs",
        primary_key=["project_slug", "timestamp"],
        write_disposition="replace",
    )

    if global_config.gcp_bigquery_enabled:
        bigquery_adapter(
            resource,
            cluster=["project_slug", "timestamp"],
        )

    yield resource
