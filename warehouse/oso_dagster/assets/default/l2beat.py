import json
import logging
import time
from typing import Any, Dict
from urllib.parse import urlparse

from dlt.sources.helpers.requests.retry import Client
from dlt.sources.rest_api.typing import RESTAPIConfig, RESTAPIConfigBase
from oso_dagster.factories.rest import create_rest_factory_asset
from requests import Response

logger = logging.getLogger(__name__)

BASE_URL: str = "https://l2beat.com/api"

DELAY_SECONDS: int = 5
REQUEST_TIMEOUT: int = 300

K8S_CONFIG: Dict[str, Any] = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
        },
    },
}


def _extract_project_slug(response: Response) -> str:
    path_segments = urlparse(response.url).path.strip("/").split("/")
    return path_segments[-1] if path_segments[-1] else path_segments[-2]


def _transform_projects_response(response: Response) -> Response:
    logger.info(
        f"Transforming projects response from {response.url} (status: {response.status_code})"
    )
    try:
        data = response.json()
        projects = data.get("projects", {})
        project_list = list(projects.values())
        logger.info(f"Successfully got {len(project_list)} projects.")
        response._content = json.dumps(project_list).encode("utf-8")
    except Exception as e:
        logger.error(f"Error transforming projects response: {e}")
        response._content = json.dumps([]).encode("utf-8")
    return response


def _extract_project_keys(response: Response) -> Response:
    logger.info(
        f"Extracting project keys from {response.url} (status: {response.status_code})"
    )
    try:
        data = response.json()
        projects = data.get("projects", {})
        project_slugs = [{"slug": slug} for slug in projects.keys()]
        logger.info(f"Successfully got {len(project_slugs)} project slugs.")
        response._content = json.dumps(project_slugs).encode("utf-8")
    except Exception as e:
        logger.error(f"Error extracting project keys: {e}")
        response._content = json.dumps([]).encode("utf-8")
    return response


def _transform_chart_response(response: Response) -> Response:
    project_slug = _extract_project_slug(response)
    logger.info(
        f"Transforming chart response for project '{project_slug}' from {response.url} (status: {response.status_code})"
    )

    try:
        data = response.json()
        if not data.get("success"):
            logger.warning(f"Got unsuccessful response for {project_slug}: {data}")
            response._content = json.dumps([]).encode("utf-8")
            time.sleep(DELAY_SECONDS)
            return response

        chart = data.get("data", {}).get("chart", {})
        types, data_points = chart.get("types", []), chart.get("data", [])

        transformed = [
            {"project_slug": project_slug, **dict(zip(types, point))}
            for point in data_points
            if len(point) == len(types)
        ]

        logger.info(
            f"Successfully got {len(transformed)} transformed points for {project_slug}."
        )
        time.sleep(DELAY_SECONDS)

        response._content = json.dumps(transformed).encode("utf-8")
    except Exception as e:
        logger.error(f"Error transforming chart response for {project_slug}: {e}")
        response._content = json.dumps([]).encode("utf-8")

    return response


rest_client = Client(
    request_timeout=REQUEST_TIMEOUT,
    raise_for_status=False,
    request_max_attempts=10,
    request_backoff_factor=1.5,
    request_max_retry_delay=30,
    respect_retry_after_header=True,
)

_BASE_CONFIG: RESTAPIConfigBase = {
    "client": {
        "base_url": BASE_URL,
        "session": rest_client.session,
    },
    "resources": [],
}

projects_config: RESTAPIConfig = {
    **_BASE_CONFIG,
    "resource_defaults": {
        "write_disposition": "replace",
        "max_table_nesting": 0,
        "endpoint": {
            "response_actions": [
                {"status_code": 404, "action": "ignore"},
                {"status_code": 429, "action": "ignore"},
            ],
        },
    },
    "resources": [
        {
            "name": "projects",
            "endpoint": {
                "path": "scaling/summary",
                "response_actions": [{"action": _transform_projects_response}],
            },
        }
    ],
}

activity_config: RESTAPIConfig = {
    **_BASE_CONFIG,
    "resource_defaults": {
        "write_disposition": "replace",
        "max_table_nesting": 0,
        "primary_key": ["project_slug", "timestamp"],
        "endpoint": {
            "params": {"range": "max"},
            "response_actions": [
                {"status_code": 404, "action": "ignore"},
                {"status_code": 429, "action": "ignore"},
            ],
        },
    },
    "resources": [
        {
            "name": "projects_slugs",
            "endpoint": {
                "path": "scaling/summary",
                "response_actions": [{"action": _extract_project_keys}],
            },
            "selected": False,
        },
        {
            "name": "activity",
            "endpoint": {
                "path": "scaling/activity/{resources.projects_slugs.slug}",
                "response_actions": [{"action": _transform_chart_response}],
            },
        },
    ],
}

tvs_config: RESTAPIConfig = {
    **_BASE_CONFIG,
    "resource_defaults": {
        "write_disposition": "replace",
        "max_table_nesting": 0,
        "primary_key": ["project_slug", "timestamp"],
        "endpoint": {
            "params": {"range": "max"},
            "response_actions": [
                {"status_code": 404, "action": "ignore"},
                {"status_code": 429, "action": "ignore"},
            ],
        },
    },
    "resources": [
        {
            "name": "projects_slugs",
            "endpoint": {
                "path": "scaling/summary",
                "response_actions": [{"action": _extract_project_keys}],
            },
            "selected": False,
        },
        {
            "name": "tvs",
            "endpoint": {
                "path": "scaling/tvs/{resources.projects_slugs.slug}",
                "response_actions": [{"action": _transform_chart_response}],
            },
        },
    ],
}

_projects_factory = create_rest_factory_asset(
    config=projects_config,
)
_activity_factory = create_rest_factory_asset(
    config=activity_config,
)
_tvs_factory = create_rest_factory_asset(
    config=tvs_config,
)

l2beat_projects_assets = _projects_factory(
    key_prefix="l2beat",
    name="projects",
    op_tags={
        "dagster/concurrency_key": "l2beat_projects",
        "dagster-k8s/config": K8S_CONFIG,
    },
)

l2beat_activity_assets = _activity_factory(
    key_prefix="l2beat",
    name="activity",
    op_tags={
        "dagster/concurrency_key": "l2beat_activity",
        "dagster-k8s/config": K8S_CONFIG,
    },
)

l2beat_tvs_assets = _tvs_factory(
    key_prefix="l2beat",
    name="tvs",
    op_tags={
        "dagster/concurrency_key": "l2beat_tvs",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
