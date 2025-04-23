import os
import typing as t
from functools import cached_property
from pathlib import Path

import requests
from oso_dagster.utils.dbt import BQTargetConfigTemplate, load_dbt_manifests
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


class DagsterConfig(BaseSettings):
    """OSO's dagster configuration"""

    model_config = SettingsConfigDict(env_prefix="dagster_")

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

    dbt_target_base_dir: str = ""

    dbt_profiles_dir: str = os.path.expanduser("~/.dbt")

    production_dbt_target: str = "production"

    dbt_impersonate_service_account: str = ""

    dbt_parse_project_on_load: bool = False

    verbose_logs: bool = False

    env: str = "dev"

    enable_bigquery: bool = False

    sqlmesh_dir: str = ""
    sqlmesh_gateway: str = "local"
    sqlmesh_catalog: str = "iceberg"
    sqlmesh_schema: str = "oso"
    sqlmesh_bq_export_dataset_id: str = "oso"

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

    @model_validator(mode="after")
    def handle_generated_config(self):
        """Handles any configurations that can be generated from other configuration values"""
        if not self.dagster_home:
            self.dagster_home = os.path.join(self.repo_dir, ".dagster_local_home")
        if not self.local_duckdb_path:
            self.local_duckdb_path = os.path.join(self.dagster_home, "local.duckdb")
        if not self.main_dbt_project_dir:
            self.main_dbt_project_dir = self.repo_dir
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

    @cached_property
    def dbt_manifests(self):
        return load_dbt_manifests(
            self.dbt_target_base_dir,
            self.main_dbt_project_dir,
            self.project_id,
            self.dbt_profile_name,
            [
                ("production", "oso"),
                ("base_playground", "oso_base_playground"),
                ("playground", "oso_playground"),
            ],
            BQTargetConfigTemplate(
                impersonate_service_account=self.dbt_impersonate_service_account
            ),
            parse_projects=self.dbt_parse_project_on_load,
        )
