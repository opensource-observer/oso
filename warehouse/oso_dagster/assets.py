import os
from typing import Any, Mapping
from dagster import AssetExecutionContext, AssetKey, asset

from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from .constants import main_dbt_manifest_path
from .goldsky import (
    GoldskyConfig,
    goldsky_asset,
)
from .factories import interval_gcs_import_asset, SourceMode, Interval, IntervalGCSAsset
from .cbt import CBTResource


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


@asset
def random_cbt(cbt: CBTResource):
    print("here i am ")
    print(cbt)
    c = cbt.get()
    print(
        c.render_model("optimism_dedupe.sql", unique_column="hello", order_column="hi")
    )


# optimism_traces_parallel = goldsky_asset(
#     "optimism_traces_parallel",
#     GoldskyConfig(
#         source_name="optimism-traces",
#         project_id="opensource-observer",
#         working_destination_dataset_name="oso_raw_sources",
#         destination_table_name="optimism_traces",
#         partition_column_name="block_number",
#         pointer_size=int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "500")),
#         bucket_key_id=os.environ.get("DUCKDB_GCS_KEY_ID"),
#         bucket_secret=os.environ.get("DUCKDB_GCS_SECRET"),
#         max_objects_to_load=int(os.environ.get("GOLDSKY_BATCH_SIZE", "1000")),
#     ),
# )

base_traces = goldsky_asset(
    "base_traces",
    GoldskyConfig(
        source_name="base-traces",
        project_id="opensource-observer",
        destination_table_name="base_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="oso_sources",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        pointer_size=int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "20000")),
        # uncomment the following value to test
        # max_objects_to_load=2,
    ),
)

optimism_traces = goldsky_asset(
    "optimism_traces",
    GoldskyConfig(
        source_name="optimism-traces",
        project_id="opensource-observer",
        destination_table_name="optimism_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="oso_sources",
        partition_column_name="block_timestamp",
        pointer_size=int(os.environ.get("GOLDSKY_CHECKPOINT_SIZE", "20000")),
        dedupe_model="optimism_dedupe.sql",
        # uncomment the following value to test
        # max_objects_to_load=2000,
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
