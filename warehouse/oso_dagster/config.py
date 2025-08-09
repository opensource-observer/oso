import os
import typing as t
from pathlib import Path

import requests
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_id() -> str:
    project_id_url = (
        "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    )
    project_id = requests.get(
        project_id_url, allow_redirects=True, headers={"Metadata-Flavor": "Google"}
    ).content.decode("utf-8")
    return project_id


def get_repo_sha() -> str:
    """If the repo_sha file exists, return its contents."""
    if os.path.exists("/oso.repo_sha.txt"):
        with open("/oso.repo_sha.txt", "r") as f:
            return f.read().strip()
    return "unknown"


class DagsterConfig(BaseSettings):
    """OSO's dagster configuration"""

    model_config = SettingsConfigDict(env_prefix="dagster_")

    # We have a `run_mode` so that some processes can be run in different modes
    # Particularly this is useful for things like our preemptive caching at
    # build time for dagster assets
    run_mode: t.Literal["serve", "build"] = "serve"

    repo_sha: str = Field(default_factory=get_repo_sha)

    project_id: str = Field(alias="GOOGLE_PROJECT_ID", default_factory=get_project_id)

    repo_dir: str = Field(
        default_factory=lambda: os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    )

    dagster_home: str = ""

    main_dbt_project_dir: str = ""
    staging_bucket_url: str = ""
    local_duckdb_path: str = ""
    dbt_profile_name: str = "opensource_observer"
    gcp_secrets_prefix: str = ""
    use_local_secrets: bool = False
    discord_webhook_url: t.Optional[str] = None
    enable_tests: bool = False
    alerts_base_url: str = ""

    gcs_bucket: str = "oso-dataset-transfer-bucket"

    # HTTP Caching used with the github repository resolver. This is a uri
    http_cache: t.Optional[str] = None

    gcp_impersonate_service_account: str = ""

    verbose_logs: bool = False

    env: str = "dev"

    enable_bigquery: bool = False

    sqlmesh_dir: str = ""
    sqlmesh_gateway: str = "local"
    sqlmesh_catalog: str = "iceberg"
    sqlmesh_schema: str = "oso"
    sqlmesh_bq_export_dataset_id: str = "oso"
    asset_cache_enabled: bool = False
    asset_cache_dir: str = ""
    asset_cache_default_ttl_seconds: int = 60 * 15

    enable_k8s_executor: bool = False

    # Setting this is different than `enable_k8s_executor`
    # `enable_k8s` is used to enable k8s resource control while
    # `enable_k8s_executor` is used to enable k8s executor for dagster
    enable_k8s: bool = False

    k8s_use_port_forward: bool = False

    trino_remote_url: str = "http://localhost:8080"
    trino_k8s_namespace: str = ""
    trino_k8s_service_name: str = ""
    trino_k8s_coordinator_deployment_name: str = ""
    trino_k8s_worker_deployment_name: str = ""
    trino_connect_timeout: int = 240

    mcs_remote_url: str = "http://localhost:8000"
    mcs_k8s_namespace: str = ""
    mcs_k8s_service_name: str = ""
    mcs_k8s_deployment_name: str = ""
    mcs_connect_timeout: int = 240

    # This is a bit of a legacy configuration that we need to remove
    cbt_search_paths: list[str] = Field(
        default_factory=lambda: [os.path.join(os.path.dirname(__file__), "models")]
    )

    clickhouse_importer_secret_group_name: str = "clickhouse_importer"
    clickhouse_secret_group_name: str = "clickhouse"

    eagerly_load_sql_tables: bool = False

    @model_validator(mode="after")
    def handle_generated_config(self):
        """Handles any configurations that can be generated from other configuration values"""
        if not self.dagster_home:
            self.dagster_home = os.path.join(self.repo_dir, ".dagster_local_home")
        if not self.local_duckdb_path:
            self.local_duckdb_path = os.path.join(self.dagster_home, "local.duckdb")
        if not self.sqlmesh_dir:
            self.sqlmesh_dir = os.path.join(self.repo_dir, "warehouse/oso_sqlmesh")

        # If we happen to be in a kubernetes environment, enable_k8s enables the
        # K8sResource to control k8s resources
        k8s_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")
        if not self.enable_k8s and k8s_service_host is not None:
            self.enable_k8s = True

        return self

    def initialize(self):
        Path(self.dagster_home).mkdir(exist_ok=True)

    @property
    def in_deployed_container(self) -> bool:
        """If the repo_sha is not unknown, we are in a deployed container."""
        return self.repo_sha != "unknown"
