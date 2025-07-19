import json
import logging
from typing import Any, Dict, Generator

import dlt
from dagster import AssetExecutionContext, ResourceParam
from dlt.destinations.adapters import bigquery_adapter
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory
import pandas as pd

logger = logging.getLogger(__name__)

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "1000m", "memory": "2Gi"},
            "limits": {"memory": "4Gi"},
        },
    },
}


def load_crypto_ecosystems_dataset(context: AssetExecutionContext) -> Generator[Dict[str, Any], None, None]:
    """
    Load parsed JSONL entries from the crypto-ecosystems GitHub dataset and yield flat records.

    Assumes the dataset has columns like:
    eco_name, branch (list), repo_url, tags (list), and optional fields.
    """
    context.log.info("Loading parsed crypto-ecosystems dataset from jsonl file")

    import pathlib
    file_path = pathlib.Path("/tmp/exports.jsonl") # Path to jsonl

    with file_path.open("r") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                # Flatten list fields
                branches = entry.get("branch", [])
                tags = entry.get("tags", [])
                for branch in (branches or [""]):
                    yield {
                        "eco_name": entry.get("eco_name", ""),
                        "branch": branch,
                        "repo_url": entry.get("repo_url", ""),
                        "tags": ",".join(tags),
                    }
            except Exception as e:
                context.log.warning(f"Failed to parse entry: {e}")

def get_all_unique_branches(context: AssetExecutionContext) -> Generator[Dict[str, Any], None, None]:
    """
    Yield all unique branches and their details in the dataset
    """
    unique_branches = set()
    for row in load_crypto_ecosystems_dataset(context):
        branch = row.get('branch', '').strip()
        if branch and branch not in unique_branches:
            repo_url = row.get('repo_url', '').strip()
            tags = row.get('tags', '').strip()
            detail = (branch, repo_url, tags)
            unique_branches.add(detail)
            yield {
                'branch': branch,
                'repo_url': repo_url,
                'tags': tags
            }

@dlt_factory(
    key_prefix="crypto_ecosystems",
    name="project_metadata",
    op_tags={
        "dagster/concurrency_key": "crypto_ecosystems_metadata",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def crypto_ecosystems_metadata_assets(
    context: AssetExecutionContext,
    global_config: ResourceParam[DagsterConfig],
):
    """
    Dagster asset for loading metadata from the crypto-ecosystems
    repository into BigQuery.
    """
    resource = dlt.resource(
        load_crypto_ecosystems_dataset(context),
        name="project_metadata",
        primary_key=["repo_url", "branch"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, cluster=["eco_name", "branch"])
    yield resource

@dlt_factory(
    key_prefix="crypto_ecosystems",
    name="",
    op_tags={
        "dagster/concurrency_key": "crypto_ecosystems_metadata",
        "dagster-k8s/config": K8S_CONFIG,
    },
)
def branch_details(
        context: AssetExecutionContext,
        global_config: ResourceParam[DagsterConfig]
):
    """
    Dagster asset that extracts and loads unique branches and their details
    from crypto-ecosystems jsonl file to BigQuery via DTL
    """
    resource = dlt.resource(
        get_all_unique_branches(context),
        name="branch_details",
        primary_key=["branch", "repo_url"],
        write_disposition="replace",
    )
    if global_config.enable_bigquery:
        bigquery_adapter(resource, cluster=["branch"])
    yield resource
