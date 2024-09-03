import os
from pathlib import Path
import requests
from .utils.dbt import (
    get_profiles_dir,
    load_dbt_manifests,
    BQTargetConfigTemplate,
)
from dotenv import load_dotenv

load_dotenv()

main_dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
repo_dir = main_dbt_project_dir

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
    except Exception:
        raise Exception("GOOGLE_PROJECT_ID must be set if you're not in GCP")

dagster_home = os.getenv("DAGSTER_HOME", os.path.join(repo_dir, ".dagster_local_home"))

# Ensure the dagster_home path exists
Path(dagster_home).mkdir(parents=True, exist_ok=True)

staging_bucket = os.getenv("DAGSTER_STAGING_BUCKET_URL")
if not staging_bucket:
    staging_bucket = f"file://{os.path.join(dagster_home, "staging")}"

local_duckdb = os.getenv("DAGSTER_LOCAL_DUCKDB_PATH")
if not local_duckdb:
    local_duckdb = os.path.join(dagster_home, "local.duckdb")

profile_name = os.getenv("DAGSTER_DBT_PROFILE_NAME", "opensource_observer")
gcp_secrets_prefix = os.getenv("DAGSTER_GCP_SECRETS_PREFIX", "")
use_local_secrets = os.getenv("DAGSTER_USE_LOCAL_SECRETS", "true").lower() in [
    "true",
    "1",
]
discord_webhook_url = os.getenv("DAGSTER_DISCORD_WEBHOOK_URL")
enable_tests = os.getenv("DAGSTER_ENABLE_TESTS", "false").lower() in ["true", "1"]
dagster_alerts_base_url = os.getenv("DAGSTER_ALERTS_BASE_URL", "")

# We can enable an HTTP caching mechanism. It can be one of the
http_cache = os.getenv("DAGSTER_HTTP_CACHE")

dbt_profiles_dir = get_profiles_dir()
dbt_target_base_dir = os.getenv("DAGSTER_DBT_TARGET_BASE_DIR") or ""
PRODUCTION_DBT_TARGET = "production"
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
verbose_logs = os.getenv("DAGSTER_VERBOSE_LOGS", "false").lower() in ["true", "1"]

env = os.getenv("DAGSTER_ENV", "dev")

enable_bigquery = os.getenv("DAGSTER_ENABLE_BIGQUERY", "false").lower() in ["true", "1"]

sqlmesh_dir = os.getenv("DAGSTER_SQLMESH_DIR", str(repo_dir.joinpath("warehouse/metrics_mesh")))
