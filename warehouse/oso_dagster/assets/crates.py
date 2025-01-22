from google.cloud.bigquery import SourceFormat
from oso_dagster.config import DagsterConfig

from ..factories import AssetFactoryResponse, early_resources_asset_factory
from ..factories.archive2bq import Archive2BqAssetConfig, create_archive2bq_asset


@early_resources_asset_factory()
def crates_data(global_config: DagsterConfig) -> AssetFactoryResponse:
    asset = create_archive2bq_asset(
        Archive2BqAssetConfig(
            key_prefix="rust",
            asset_name="crates",
            source_url="https://static.crates.io/db-dump.tar.gz",
            source_format=SourceFormat.CSV,
            filter_fn=lambda file: file.endswith(".csv"),
            schema_overrides={
                "crates": {
                    "id": "INTEGER",
                }
            },
            staging_bucket=global_config.staging_bucket_url,
            dataset_id="crates",
            deps=[],
        )
    )
    return asset
