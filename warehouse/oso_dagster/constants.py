import os
from pathlib import Path
from typing import Dict, List
import pathlib

import requests
from dagster import DefaultSensorStatus
from dagster_dbt import DbtCliResource

main_dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()

# Leaving this for now as it allows a separate source related dbt model
# source_dbt_project_dir = Path(__file__).joinpath("..", "..", "source_dbt").resolve()
# source_dbt = DbtCliResource(project_dir=os.fspath(source_dbt_project_dir))

generated_profiles_yml = """
opensource_observer:
  target: production
  outputs:
    production:
      type: bigquery
      dataset: oso
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: %(project_id)s
      threads: 32
    base_playground:
      type: bigquery
      dataset: oso_base_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: %(project_id)s
      threads: 32
    playground:
      type: bigquery
      dataset: oso_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: %(project_id)s
      threads: 32
"""


def get_profiles_dir():
    return os.environ.get("DBT_PROFILES_DIR", os.path.expanduser("~/.dbt"))


def generate_profile_and_auth():
    profiles_path = os.path.join(get_profiles_dir(), "profiles.yml")

    Path(os.path.dirname(profiles_path)).mkdir(parents=True, exist_ok=True)

    service_account_path = os.path.expanduser("~/service-account.json")
    Path(os.path.dirname(service_account_path)).mkdir(parents=True, exist_ok=True)

    print(f"writing dbt profile to {profiles_path}")

    project_id_url = (
        "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    )
    project_id = requests.get(
        project_id_url, allow_redirects=True, headers={"Metadata-Flavor": "Google"}
    ).content.decode("utf-8")
    with open(profiles_path, "w") as f:
        f.write(
            generated_profiles_yml
            % dict(service_account_path=service_account_path, project_id=project_id)
        )


def load_dbt_manifests(targets: List[str]) -> Dict[str, str]:
    manifests: Dict[str, str] = dict()
    dbt_target_base_dir = os.getenv("DAGSTER_DBT_TARGET_BASE_DIR")

    # If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at
    # run time. Otherwise, we error for now. Eventually the manifests should be
    # generated during container creation so this doesn't need to run every time
    # a docker container loads.
    if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD") or os.getenv(
        "DAGSTER_DBT_GENERATE_AND_AUTH_GCP"
    ):
        if os.getenv("DAGSTER_DBT_GENERATE_AND_AUTH_GCP"):
            generate_profile_and_auth()
        for target in targets:
            target_path = Path(dbt_target_base_dir, target)
            # Ensure the dbt_target_base_dir exists
            pathlib.Path(dbt_target_base_dir).mkdir(parents=True, exist_ok=True)

            dbt = DbtCliResource(
                project_dir=os.fspath(main_dbt_project_dir), target=target
            )
            manifests[target] = (
                dbt.cli(
                    ["--quiet", "parse"],
                    target_path=target_path,
                )
                .wait()
                .target_path.joinpath("manifest.json")
            )
    else:
        raise NotImplementedError("Currently we must generate dbt manifests")
    return manifests


dbt_profiles_dir = get_profiles_dir()
main_dbt_manifests = load_dbt_manifests(["production", "base_playground", "playground"])
