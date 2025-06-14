---
title: Import from Google Cloud Storage (GCS)
sidebar_position: 6
---

# Import from Google Cloud Storage (GCS)

This guide explains how to import data into OSO using Google Cloud Storage (GCS). This method is ideal for partners who can provide regular data updates in a structured format.

## Overview

We strongly prefer data partners that can provide updated live datasets over static snapshots. Datasets that use this method will require OSO sponsorship for storing the data, as we take on the costs of converting it into a BigQuery dataset and associated long-term storage costs.

If you believe your data storage qualifies to be sponsored by OSO, please reach out to us on [Discord](https://www.opensource.observer/discord).

:::note Alternative Options
If you prefer to handle the data storage yourself, check out the [Connect via BigQuery guide](./bq-data-transfer.md).
:::

## Getting Started

### 1. Set Up GCS Access

Coordinate with the OSO engineering team directly on [Discord](https://www.opensource.observer/discord) to:

- Get write permissions to our GCS bucket
- Set up your Google service account
- Configure necessary access controls

### 2. Schedule Data Updates

Set up a cron job to regularly dump new time-partitioned data. Common schedules include:

- Daily updates for frequently changing data
- Weekly updates for more stable datasets
- Custom schedules based on your data update frequency

## Creating Your Asset

### Basic Structure

Create a new asset file in `warehouse/oso_dagster/assets/` that uses the GCS asset factory. Here's the basic structure:

```python
from ..factories import (
    interval_gcs_import_asset,
    SourceMode,
    TimeInterval,
    IntervalGCSAsset,
)

your_asset = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="your_prefix",
        name="your_asset_name",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="your_data_path",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/your_file.parquet",
        destination_table="your_table_name",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="your_dataset",
        interval=TimeInterval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
        format="PARQUET",
    ),
)
```

### Configuration Parameters

For the latest documentation on configuration parameters, check out the comments in the [GCS factory](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/factories/gcs.py).

## Example Patterns

Here are some real-world examples showing different patterns for GCS data import:

### 1. Loading Parquet Files from URL

The Open Labels Initiative asset demonstrates how to load Parquet files directly from a URL:

```python
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
```

This example shows how to:

- Load Parquet files directly from a URL
- Skip uncompression for already uncompressed files
- Use a staging bucket for temporary storage

### 2. Handling Compressed Data Files

The Crates.io asset demonstrates how to handle compressed data files with filtering and schema overrides:

```python
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
```

This example shows how to:

- Load compressed data (tar.gz)
- Filter specific files from an archive using `filter_fn`
- Override schema types for specific columns
- Handle CSV format data

## Additional Examples

In the [OSO monorepo](https://github.com/opensource-observer/oso), you'll find more examples:

- [Superchain data](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/__init__.py)
- [OpenRank reputations on Farcaster](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/karma3.py)

## Next Steps

1. Review the [GCS factory](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/factories/gcs.py) for detailed configuration options
2. Set up your data pipeline to regularly export to GCS
3. Create your asset file in the `warehouse/oso_dagster/assets/` directory
4. Test your asset locally using the [Dagster tutorial](https://docs.dagster.io/tutorial)

Need help? Reach out to us on [Discord](https://www.opensource.observer/discord).
