import os
from typing import Any, Mapping, Dict, List
from dagster import AssetExecutionContext, AssetKey, asset, AssetsDefinition, Config

from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from google.cloud.bigquery.schema import SchemaField
from .constants import main_dbt_manifests, main_dbt_project_dir, dbt_profiles_dir
from .factories.goldsky import (
    GoldskyConfig,
    goldsky_asset,
    traces_checks,
    transactions_checks,
    blocks_checks,
)
from .factories import interval_gcs_import_asset, SourceMode, Interval, IntervalGCSAsset


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        prefix: str,
        internal_schema_map: Dict[str, str],
    ):
        self._prefix = prefix
        self._internal_schema_map = internal_schema_map

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        asset_key = super().get_asset_key(dbt_resource_props)
        final_key = asset_key.with_prefix(self._prefix)
        # This is a temporary hack to get ossd as a top level item in production
        if (
            dbt_resource_props.get("source_name", "") == "ossd"
            and dbt_resource_props["schema"] == "oso"
            and dbt_resource_props.get("identifier", "").endswith("_ossd")
        ):
            return asset_key
        if dbt_resource_props["resource_type"] == "source":
            schema = dbt_resource_props["schema"]
            if schema in self._internal_schema_map:
                new_key = self._internal_schema_map[schema][:]
                new_key.append(dbt_resource_props["identifier"])
                final_key = AssetKey(new_key)
            else:
                final_key = asset_key
        return final_key


class DBTConfig(Config):
    full_refresh: bool = False


def dbt_assets_from_manifests_map(
    project_dir: str,
    manifests: Dict[str, str],
    internal_map: Dict[str, List[str]] = None,
) -> List[AssetsDefinition]:
    if not internal_map:
        internal_map = {}
    assets: List[AssetsDefinition] = []
    for target, manifest_path in manifests.items():
        print(f"Target[{target}] using profiles dir {dbt_profiles_dir}")

        translator = CustomDagsterDbtTranslator(["dbt", target], internal_map)

        @dbt_assets(
            name=f"{target}_dbt",
            manifest=manifest_path,
            dagster_dbt_translator=translator,
        )
        def _generated_dbt_assets(context: AssetExecutionContext, config: DBTConfig):
            print(f"using profiles dir {dbt_profiles_dir}")
            dbt = DbtCliResource(
                project_dir=os.fspath(project_dir),
                target=target,
                profiles_dir=dbt_profiles_dir,
            )
            build_args = ["build"]
            if config.full_refresh:
                build_args += ["--full-refresh"]
            yield from dbt.cli(build_args, context=context).stream()

        assets.append(_generated_dbt_assets)

    return assets


all_dbt_assets = dbt_assets_from_manifests_map(
    main_dbt_project_dir,
    main_dbt_manifests,
    {
        "oso": ["dbt", "production"],
        "oso_base_playground": ["dbt", "base_playground"],
        "oso_playground": ["dbt", "playground"],
    },
)


base_blocks = goldsky_asset(
    GoldskyConfig(
        key_prefix="base",
        name="blocks",
        source_name="base-blocks",
        project_id="opensource-observer",
        destination_table_name="base_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[blocks_checks()],
    ),
)

base_transactions = goldsky_asset(
    GoldskyConfig(
        key_prefix="base",
        name="transactions",
        source_name="base-enriched_transactions",
        project_id="opensource-observer",
        destination_table_name="base_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        checks=[transactions_checks("opensource-observer.superchain.base_blocks")],
    ),
    deps=base_blocks.assets,
)

base_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="base",
        name="traces",
        source_name="base-traces",
        project_id="opensource-observer",
        destination_table_name="base_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[traces_checks("opensource-observer.superchain.base_transactions")],
    ),
    deps=base_transactions.assets,
)

frax_blocks = goldsky_asset(
    GoldskyConfig(
        key_prefix="frax",
        name="blocks",
        source_name="frax-blocks",
        project_id="opensource-observer",
        destination_table_name="frax_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[blocks_checks()],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

frax_transactions = goldsky_asset(
    GoldskyConfig(
        key_prefix="frax",
        name="transactions",
        source_name="frax-receipt_transactions",
        project_id="opensource-observer",
        destination_table_name="frax_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        checks=[transactions_checks("opensource-observer.superchain.frax_blocks")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=frax_blocks.assets,
)

frax_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="frax",
        name="traces",
        source_name="frax-traces",
        project_id="opensource-observer",
        destination_table_name="frax_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[traces_checks("opensource-observer.superchain.frax_transactions")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=frax_transactions.assets,
)

mode_blocks = goldsky_asset(
    GoldskyConfig(
        key_prefix="mode",
        name="blocks",
        source_name="mode-blocks",
        project_id="opensource-observer",
        destination_table_name="mode_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[blocks_checks()],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

mode_transactions = goldsky_asset(
    GoldskyConfig(
        key_prefix="mode",
        name="transactions",
        source_name="mode-receipt_transactions",
        project_id="opensource-observer",
        destination_table_name="mode_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        checks=[transactions_checks("opensource-observer.superchain.mode_blocks")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=mode_blocks.assets,
)

mode_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="mode",
        name="traces",
        source_name="mode-traces",
        project_id="opensource-observer",
        destination_table_name="mode_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[traces_checks("opensource-observer.superchain.mode_transactions")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=mode_transactions.assets,
)

metal_blocks = goldsky_asset(
    GoldskyConfig(
        key_prefix="metal",
        name="blocks",
        source_name="metal-blocks",
        project_id="opensource-observer",
        destination_table_name="metal_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[blocks_checks()],
    ),
)

metal_transactions = goldsky_asset(
    GoldskyConfig(
        key_prefix="metal",
        name="transactions",
        source_name="metal-receipt_transactions",
        project_id="opensource-observer",
        destination_table_name="metal_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        checks=[transactions_checks("opensource-observer.superchain.metal_blocks")],
    ),
    deps=metal_blocks.assets,
)


metal_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="metal",
        name="traces",
        source_name="metal-traces",
        project_id="opensource-observer",
        destination_table_name="metal_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[traces_checks("opensource-observer.superchain.metal_transactions")],
    ),
    deps=metal_transactions.assets,
)

optimism_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="optimism",
        name="traces",
        source_name="optimism-traces",
        project_id="opensource-observer",
        destination_table_name="optimism_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        dedupe_model="optimism_dedupe.sql",
        checks=[
            traces_checks(
                "bigquery-public-data.goog_blockchain_optimism_mainnet_us.transactions",
                transactions_transaction_hash_column_name="transaction_hash",
            )
        ],
        # uncomment the following value to test
        # max_objects_to_load=2000,
    ),
)

pgn_blocks = goldsky_asset(
    GoldskyConfig(
        key_prefix="pgn",
        name="blocks",
        source_name="pgn-blocks",
        project_id="opensource-observer",
        destination_table_name="pgn_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[blocks_checks()],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

pgn_transactions = goldsky_asset(
    GoldskyConfig(
        key_prefix="pgn",
        name="transactions",
        source_name="pgn-enriched_transactions",
        project_id="opensource-observer",
        destination_table_name="pgn_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        checks=[transactions_checks("opensource-observer.superchain.pgn_blocks")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=pgn_blocks.assets,
)

pgn_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="pgn",
        name="traces",
        source_name="pgn-traces",
        project_id="opensource-observer",
        destination_table_name="pgn_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[traces_checks("opensource-observer.superchain.pgn_transactions")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=pgn_transactions.assets,
)

zora_blocks = goldsky_asset(
    GoldskyConfig(
        key_prefix="zora",
        name="blocks",
        source_name="zora-blocks",
        project_id="opensource-observer",
        destination_table_name="zora_blocks",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[blocks_checks()],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
)

zora_transactions = goldsky_asset(
    GoldskyConfig(
        key_prefix="zora",
        name="transactions",
        source_name="zora-enriched_transactions",
        project_id="opensource-observer",
        destination_table_name="zora_transactions",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        schema_overrides=[SchemaField(name="value", field_type="BYTES")],
        checks=[transactions_checks("opensource-observer.superchain.zora_blocks")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=zora_blocks.assets,
)

zora_traces = goldsky_asset(
    GoldskyConfig(
        key_prefix="zora",
        name="traces",
        source_name="zora-traces",
        project_id="opensource-observer",
        destination_table_name="zora_traces",
        working_destination_dataset_name="oso_raw_sources",
        destination_dataset_name="superchain",
        partition_column_name="block_timestamp",
        partition_column_transform=lambda c: f"TIMESTAMP_SECONDS(`{c}`)",
        checks=[traces_checks("opensource-observer.superchain.zora_transactions")],
        # uncomment the following value to test
        # max_objects_to_load=1,
    ),
    deps=zora_transactions.assets,
)


karma3_globaltrust = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="karma3",
        name="globaltrust",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openrank",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust.csv.gz",
        destination_table="globaltrust",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="karma3",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
    ),
)

karma3_globaltrust_config = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="karma3",
        name="globaltrust_config",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openrank",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_globaltrust_config.csv.gz",
        destination_table="globaltrust_config",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="karma3",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
    ),
)

karma3_localtrust = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="karma3",
        name="localtrust",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="openrank",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/k3l_cast_localtrust.csv.gz",
        destination_table="localtrust",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="karma3",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
    ),
)

gitcoin_passport_scores = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="gitcoin",
        name="passport_scores",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="passport",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/scores.parquet",
        destination_table="passport_scores",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="gitcoin",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
        format="PARQUET",
    ),
)
