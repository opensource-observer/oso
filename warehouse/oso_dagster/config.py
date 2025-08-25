import os
import typing as t
from pathlib import Path

import requests
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


import logging
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class GCPMetadataError(Exception):
    """Custom exception for GCP metadata server errors."""
    pass

def create_requests_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    status_forcelist: tuple = (500, 502, 503, 504),
) -> requests.Session:
    """Create a requests session with retry configuration.
    
    Args:
        retries: Number of retries for failed requests
        backoff_factor: Backoff factor between retries
        status_forcelist: HTTP status codes to retry on
        
    Returns:
        requests.Session: Configured session object
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_project_id(timeout: int = 5, retries: int = 3) -> str:
    """Retrieve GCP project ID from metadata server with robust error handling.
    
    Args:
        timeout: Request timeout in seconds
        retries: Number of retries for failed requests
        
    Returns:
        str: GCP project ID
        
    Raises:
        GCPMetadataError: If unable to retrieve project ID after retries
    """
    project_id_url = (
        "http://metadata.google.internal/computeMetadata/v1/project/project-id"
    )
    headers = {
        "Metadata-Flavor": "Google"
    }
    
    session = create_requests_session(retries=retries)
    
    try:
        response = session.get(
            project_id_url,
            timeout=timeout,
            headers=headers,
            allow_redirects=True
        )
        response.raise_for_status()
        
        project_id = response.content.decode("utf-8").strip()
        if not project_id:
            raise GCPMetadataError("Empty project ID received from metadata server")
            
        logger.debug(f"Successfully retrieved GCP project ID: {project_id}")
        return project_id
        
    except Timeout:
        error_msg = f"Timeout ({timeout}s) while connecting to GCP metadata server"
        logger.error(error_msg)
        raise GCPMetadataError(error_msg)
        
    except ConnectionError as e:
        error_msg = f"Failed to connect to GCP metadata server: {str(e)}"
        logger.error(error_msg)
        raise GCPMetadataError(error_msg)
        
    except RequestException as e:
        error_msg = f"Error retrieving GCP project ID: {str(e)}"
        logger.error(error_msg)
        raise GCPMetadataError(error_msg)
        
    finally:
        session.close()


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

    gcp_enabled: bool = Field(default=False)

    repo_sha: str = Field(default_factory=get_repo_sha)

    gcp_project_id_override: str = Field(alias="GOOGLE_PROJECT_ID", default="")

    repo_dir: str = Field(
        default_factory=lambda: os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
    )

    dagster_home: str = Field(alias="DAGSTER_HOME", default="")

    main_dbt_project_dir: str = ""
    staging_bucket_url: str = ""
    local_duckdb_path: str = ""
    dbt_profile_name: str = "opensource_observer"
    gcp_secrets_prefix: str = ""
    use_local_secrets: bool = True
    discord_webhook_url: t.Optional[str] = None
    test_assets_enabled: bool = False
    alerts_base_url: str = ""

    gcs_bucket: str = "oso-dataset-transfer-bucket"

    # HTTP Caching used with the github repository resolver. This is a uri
    http_cache: t.Optional[str] = None

    gcp_impersonate_service_account: str = ""

    verbose_logs: bool = False

    env: str = "dev"

    gcp_bigquery_enabled: bool = False

  

    k8s_executor_enabled: bool = False

    # Setting this is different than `k8s_executor_enabled`
    # `k8s_enabled` is used to enable k8s resource control while
    # `k8s_executor_enabled` is used to enable k8s executor for dagster
    k8s_enabled: bool = False

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

   

        # If we happen to be in a kubernetes environment, k8s_enabled enables the
        # K8sResource to control k8s resources
        k8s_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")
        if not self.k8s_enabled and k8s_service_host is not None:
            self.k8s_enabled = True

        if self.env == "production":
            self.sqlmesh_assets_on_default_code_location_enabled = True

        return self

    def initialize(self):
        Path(self.dagster_home).mkdir(exist_ok=True)

    @property
    def gcp_project_id(self):
        if self.gcp_project_id_override:
            return self.gcp_project_id_override
        if not self.gcp_enabled:
            raise ValueError(
                "In order to automatically discover a project id you must explicitly enable gcp."
            )
        return get_project_id()

    @property
    def in_deployed_container(self) -> bool:
        """If the repo_sha is not unknown, we are in a deployed container."""
        return self.repo_sha != "unknown"
