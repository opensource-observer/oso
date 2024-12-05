from google.cloud.bigquery import SourceFormat
from ..constants import staging_bucket
from ..factories.archive2bq import Archive2BqAssetConfig, create_archive2bq_asset

crates_data = create_archive2bq_asset(
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
        staging_bucket=staging_bucket,
        dataset_id="crates",
        deps=[],
    )
)
