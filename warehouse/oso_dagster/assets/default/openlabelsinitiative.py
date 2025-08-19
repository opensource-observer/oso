from google.cloud.bigquery import SourceFormat
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import AssetFactoryResponse, early_resources_asset_factory
from oso_dagster.factories.archive2bq import (
    Archive2BqAssetConfig,
    create_archive2bq_asset,
)


@early_resources_asset_factory()
def openlabelsinitiative_data(global_config: DagsterConfig) -> AssetFactoryResponse:
    asset = create_archive2bq_asset(
        Archive2BqAssetConfig(
            key_prefix="openlabelsinitiative",
            dataset_id="openlabelsinitiative",
            asset_name="labels_decoded",
            source_url="https://api.growthepie.xyz/v1/oli/labels_decoded.parquet",
            source_format=SourceFormat.PARQUET,
            staging_bucket=global_config.staging_bucket_url,
            skip_uncompression=True,
            deps=[],
        )
    )
    return asset
