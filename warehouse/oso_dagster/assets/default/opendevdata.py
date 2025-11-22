import requests
from google.cloud.bigquery import SourceFormat
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import early_resources_asset_factory
from oso_dagster.factories.archive2bq import (
    Archive2BqAssetConfig,
    create_archive2bq_asset,
)

MANIFEST_URL = "https://data.opendevdata.org/manifest.json"
DATASET_ID = "opendevdata"


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
        r["path"]
        if r["path"].startswith("http")
        else f"https://data.opendevdata.org{r['path']}"
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
            deps=[],
        )
    )
    return asset
