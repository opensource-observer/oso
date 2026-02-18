import requests
from dagster import RetryPolicy
from google.cloud.bigquery import SourceFormat
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import early_resources_asset_factory
from oso_dagster.factories.archive2bq import (
    Archive2BqAssetConfig,
    create_archive2bq_asset,
)

MAX_RETRY_COUNT = 10

MANIFEST_URL = "https://data.opendevdata.org/manifest.json"
DATASET_ID = "opendevdata"

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "500m", "memory": "2048Mi"},
            "limits": {"memory": "4096Mi"},
        }
    },
    "pod_spec_config": {
        "node_selector": {"pool_type": "spot"},
        "tolerations": [
            {
                "key": "pool_type",
                "operator": "Equal",
                "value": "spot",
                "effect": "NoSchedule",
            }
        ],
    },
}


def _fetch_manifest() -> dict:
    resp = requests.get(MANIFEST_URL, timeout=60)
    resp.raise_for_status()
    return resp.json()


@early_resources_asset_factory()
def opendevdata(global_config: DagsterConfig):
    """Build an archive2bq asset from the Open Dev Data manifest."""

    manifest = _fetch_manifest()
    resources = manifest["dataset"]["resources"]

    source_urls = [
        (
            r["path"]
            if r["path"].startswith("http")
            else f"https://data.opendevdata.org{r['path']}"
        )
        for r in resources
    ]

    asset = create_archive2bq_asset(
        Archive2BqAssetConfig(
            key_prefix="opendevdata",
            dataset_id=DATASET_ID,
            asset_name="opendevdata",
            source_url=source_urls,
            source_format=SourceFormat.PARQUET,
            staging_bucket=global_config.gcs_bucket,
            skip_uncompression=True,
            sequential=True,
            deps=[],
            asset_kwargs={
                "tags": {
                    "opensource.observer/source": "weekly",
                },
                "op_tags": {
                    "dagster-k8s/config": K8S_CONFIG,
                },
                "retry_policy": RetryPolicy(max_retries=MAX_RETRY_COUNT),
            },
        )
    )
    return asset
