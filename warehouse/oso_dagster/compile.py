"""
Tool for handling dbt compilation in a docker container
"""

import click
import os
import base64
import dotenv
from pathlib import Path

dotenv.load_dotenv()

from .utils.dbt import load_dbt_manifests, BQTargetConfigTemplate, default_profiles_path


@click.command()
@click.option("--additional-vars")
def main(additional_vars: str):
    if additional_vars:
        dotenv.load_dotenv(additional_vars)
    dummy_creds_json_base64 = os.environ.get(
        "PUBLIC_GOOGLE_TEST_DUMMY_CREDENTIALS_JSON"
    )
    if not dummy_creds_json_base64:
        raise Exception("Need google test dummy credentials to compile the manifests")

    dummy_creds_json = base64.b64decode(dummy_creds_json_base64)

    # Load the credentials file
    dummy_creds_path = os.path.expanduser("~/dummy_creds.json")
    with open(dummy_creds_path, "wb") as f:
        f.write(dummy_creds_json)

    main_dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
    dbt_target_base_dir = os.getenv("DAGSTER_DBT_TARGET_BASE_DIR")
    if not dbt_target_base_dir:
        raise Exception("dbt target base directory must be set")
    load_dbt_manifests(
        dbt_target_base_dir,
        main_dbt_project_dir,
        "opensource-observer",
        "opensource_observer",
        [
            ("production", "oso"),
            ("base_playground", "oso_base_playground"),
            ("playground", "oso_playground"),
        ],
        BQTargetConfigTemplate(
            method="service-account",
            keyfile=dummy_creds_path,
        ),
        parse_projects=True,
    )
    os.remove(dummy_creds_path)
    os.remove(default_profiles_path())


if __name__ == "__main__":
    main()
