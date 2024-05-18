import os
from pathlib import Path

import requests
from dagster_dbt import DbtCliResource

main_dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
main_dbt = DbtCliResource(project_dir=os.fspath(main_dbt_project_dir))

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
      method: service-account
      keyfile: %(service_account_path)s
      project: %(project_id)s
      threads: 32
    base_playground:
      type: bigquery
      dataset: oso_base_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: service-account
      keyfile: %(service_account_path)s
      project: %(project_id)s
      threads: 32
    playground:
      type: bigquery
      dataset: oso_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: service-account
      keyfile: %(service_account_path)s
      project: %(project_id)s
      threads: 32
"""


def generate_profile_and_auth():
    profiles_path = os.path.expanduser("~/.dbt/profiles.yml")
    Path(os.path.dirname(profiles_path)).mkdir(parents=True, exist_ok=True)

    service_account_path = os.path.expanduser("~/service-account.json")
    Path(os.path.dirname(service_account_path)).mkdir(parents=True, exist_ok=True)

    print(f"writing dbt profile to {profiles_path}")

    token_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
    r = requests.get(
        token_url, allow_redirects=True, headers={"Metadata-Flavor": "Google"}
    )
    open(service_account_path, "wb").write(r.content)
    project_id_url = (
        "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    )
    project_id = requests.get(
        project_id_url, allow_redirects=True, headers={"Metadata-Flavor": "Google"}
    ).content
    with open(profiles_path, "w") as f:
        f.write(
            generated_profiles_yml
            % dict(service_account_path=service_account_path, project_id=project_id)
        )


# If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at run time.
# Otherwise, we expect a manifest to be present in the project's target directory.
if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD") or os.getenv(
    "DAGSTER_DBT_GENERATE_AND_AUTH_GCP"
):
    if os.getenv("DAGSTER_DBT_GENERATE_AND_AUTH_GCP"):
        generate_profile_and_auth()
    main_dbt_manifest_path = (
        main_dbt.cli(
            ["--quiet", "parse"],
            target_path=Path("target"),
        )
        .wait()
        .target_path.joinpath("manifest.json")
    )
    # source_dbt_manifest_path = (
    #     source_dbt.cli(
    #         ["--quiet", "parse"],
    #         target_path=Path("target"),
    #     )
    #     .wait()
    #     .target_path.joinpath("manifest.json")
    # )
    # print(f"THE PATH {source_dbt_manifest_path}")
else:
    main_dbt_manifest_path = main_dbt_project_dir.joinpath("target", "manifest.json")
    # source_dbt_manifest_path = source_dbt_project_dir.joinpath(
    #     "target", "manifest.json"
    # )
