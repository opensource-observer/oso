from google.cloud.bigquery import SourceFormat
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import AssetFactoryResponse, early_resources_asset_factory
from oso_dagster.factories.archive2bq import (
    Archive2BqAssetConfig,
    create_archive2bq_asset,
)


@early_resources_asset_factory()
def crypto_ecosystems_data(global_config: DagsterConfig) -> AssetFactoryResponse:
    asset = create_archive2bq_asset(
        Archive2BqAssetConfig(
            key_prefix="crypto_ecosystems",
            dataset_id="crypto_ecosystems",
            asset_name="taxonomy",
            source_url="https://github.com/opensource-observer/crypto-ecosystems/archive/refs/heads/master.zip",
            source_format=SourceFormat.NEWLINE_DELIMITED_JSON,
            staging_bucket=global_config.staging_bucket_url,
            filter_fn=lambda file: file.endswith(".jsonl"),
            combine_files=True,
            deps=[],
        )
    )
    return asset
