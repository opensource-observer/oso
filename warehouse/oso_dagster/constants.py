import os
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from dagster import DefaultSensorStatus
from dagster_dbt import DbtCliResource

from .utils.dbt import (
    get_profiles_dir,
    load_dbt_manifests,
    BQTargetConfigTemplate,
)

main_dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()

# Leaving this for now as it allows a separate source related dbt model
# source_dbt_project_dir = Path(__file__).joinpath("..", "..", "source_dbt").resolve()
# source_dbt = DbtCliResource(project_dir=os.fspath(source_dbt_project_dir))


def get_project_id():
    project_id_url = (
        "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    )
    project_id = requests.get(
        project_id_url, allow_redirects=True, headers={"Metadata-Flavor": "Google"}
    ).content.decode("utf-8")
    return project_id


project_id = os.getenv("GOOGLE_PROJECT_ID")

if not project_id:
    try:
        project_id = get_project_id()
    except:
        raise Exception("GOOGLE_PROJECT_ID must be set if you're not in GCP")


profile_name = os.getenv("DAGSTER_DBT_PROFILE_NAME", "opensource_observer")

dbt_profiles_dir = get_profiles_dir()
dbt_target_base_dir = os.getenv("DAGSTER_DBT_TARGET_BASE_DIR") or ""
main_dbt_manifests = load_dbt_manifests(
    dbt_target_base_dir,
    main_dbt_project_dir,
    project_id,
    profile_name,
    [
        ("production", "oso"),
        ("base_playground", "oso_base_playground"),
        ("playground", "oso_playground"),
    ],
    BQTargetConfigTemplate(
        impersonate_service_account=os.getenv(
            "DAGSTER_DBT_IMPERSONATE_SERVICE_ACCOUNT", ""
        )
    ),
    parse_projects=os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", "0") == "1",
)
