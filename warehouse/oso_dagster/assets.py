import os
from typing import Any, Mapping
from dagster import AssetExecutionContext, AssetKey, asset

from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from google.cloud.bigquery.schema import SchemaField
from .constants import main_dbt_manifest_path
from .goldsky import (
    GoldskyConfig,
    goldsky_asset,
)
from .factories import interval_gcs_import_asset, SourceMode, Interval, IntervalGCSAsset


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        return super().get_asset_key(dbt_resource_props).with_prefix(self._prefix)


@dbt_assets(
    manifest=main_dbt_manifest_path,
    dagster_dbt_translator=CustomDagsterDbtTranslator("main"),
)
def main_dbt_assets(context: AssetExecutionContext, main_dbt: DbtCliResource):
    yield from main_dbt.cli(["build"], context=context).stream()


# @dbt_assets(
#     manifest=source_dbt_manifest_path,
#     dagster_dbt_translator=CustomDagsterDbtTranslator("sources"),
# )
# def source_dbt_assets(context: AssetExecutionContext, source_dbt: DbtCliResource):
#     yield from source_dbt.cli(["build"], context=context).stream()


base_blocks = goldsky_asset(
    "base_blocks",
    GoldskyConfig(
        source_name="base-blocks",
        project_id="opensource-observer",
        destination_table_name="base_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
    ),
)

base_transactions = goldsky_asset(
    "base_transactions",
    GoldskyConfig(
        source_name="base-enriched_transactions",
        project_id="opensource-observer",
        destination_table_name="base_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        # uncomment the following value to test
    ),
)

base_traces = goldsky_asset(
    "base_traces",
    GoldskyConfig(
        source_name="base-traces",
        project_id="opensource-observer",
        destination_table_name="base_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=2,
    ),
)

frax_blocks = goldsky_asset(
    "frax_blocks",
    GoldskyConfig(
        source_name="frax-blocks",
        project_id="opensource-observer",
        destination_table_name="frax_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

frax_transactions = goldsky_asset(
    "frax_transactions",
    GoldskyConfig(
        source_name="frax-receipt_transactions",
        project_id="opensource-observer",
        destination_table_name="frax_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

frax_traces = goldsky_asset(
    "frax_traces",
    GoldskyConfig(
        source_name="frax-traces",
        project_id="opensource-observer",
        destination_table_name="frax_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

mode_blocks = goldsky_asset(
    "mode_blocks",
    GoldskyConfig(
        source_name="mode-blocks",
        project_id="opensource-observer",
        destination_table_name="mode_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

mode_transactions = goldsky_asset(
    "mode_transactions",
    GoldskyConfig(
        source_name="mode-receipt_transactions",
        project_id="opensource-observer",
        destination_table_name="mode_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

mode_traces = goldsky_asset(
    "mode_traces",
    GoldskyConfig(
        source_name="mode-traces",
        project_id="opensource-observer",
        destination_table_name="mode_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

optimism_traces = goldsky_asset(
    "optimism_traces",
    GoldskyConfig(
        source_name="optimism-traces",
        project_id="opensource-observer",
        destination_table_name="optimism_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        dedupe_model="optimism_dedupe.sql",
        # uncomment the following value to test
        # max_objects_to_load=2000,
    ),
)

pgn_blocks = goldsky_asset(
    "pgn_blocks",
    GoldskyConfig(
        source_name="pgn-blocks",
        project_id="opensource-observer",
        destination_table_name="pgn_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

pgn_transactions = goldsky_asset(
    "pgn_transactions",
    GoldskyConfig(
        source_name="pgn-enriched_transactions",
        project_id="opensource-observer",
        destination_table_name="pgn_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

pgn_traces = goldsky_asset(
    "pgn_traces",
    GoldskyConfig(
        source_name="pgn-traces",
        project_id="opensource-observer",
        destination_table_name="pgn_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

zora_blocks = goldsky_asset(
    "zora_blocks",
    GoldskyConfig(
        source_name="zora-blocks",
        project_id="opensource-observer",
        destination_table_name="zora_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

zora_transactions = goldsky_asset(
    "zora_transactions",
    GoldskyConfig(
        source_name="zora-enriched_transactions",
        project_id="opensource-observer",
        destination_table_name="zora_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

zora_traces = goldsky_asset(
    "zora_traces",
    GoldskyConfig(
        source_name="zora-traces",
        project_id="opensource-observer",
        destination_table_name="zora_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)


karma3_globaltrust = interval_gcs_import_asset(
    "karma3_globaltrust",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust.csv.gz",
        "karma3__globaltrust",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

karma3_globaltrust_config = interval_gcs_import_asset(
    "karma3_globaltrust_config",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust_config.csv.gz",
        "karma3__globaltrust_config",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

karma3_localtrust = interval_gcs_import_asset(
    "karma3_localtrust",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "openrank",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_localtrust.csv.gz",
        "karma3__localtrust",
        "oso_raw_sources",
        "oso_sources",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)

gitcoin_passport_scores = interval_gcs_import_asset(
    "gitcoin_passport_scores",
    IntervalGCSAsset(
        "opensource-observer",
        "oso-dataset-transfer-bucket",
        "passport",
        r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/scores.parquet",
        "scores",
        "oso_raw_sources",
        "passport",
        Interval.Daily,
        SourceMode.Overwrite,
        10,
    ),
)
