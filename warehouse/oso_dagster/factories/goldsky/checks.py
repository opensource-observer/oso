import os
from typing import List
from dataclasses import dataclass

from .config import GoldskyConfig, CheckFactory
from dagster import (
    AssetsDefinition,
    asset_check,
    AssetChecksDefinition,
    AssetCheckExecutionContext,
    AssetCheckResult,
    AssetCheckSeverity,
)
from dagster_gcp import BigQueryResource
from ...cbt import CBTResource


def generated_asset_prefix(asset: AssetsDefinition):
    return "_".join(asset.key.path)


def block_number_check(
    block_number_column_name: str, config: GoldskyConfig, asset: AssetsDefinition
) -> AssetChecksDefinition:
    prefix = generated_asset_prefix(asset)

    @asset_check(name=f"{prefix}_block_number_check", asset=asset)
    def _block_number_check(
        context: AssetCheckExecutionContext,
        cbt: CBTResource,
    ):
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        block_number_results = list(
            c.query(
                "block_number_check.sql",
                block_number_column_name=block_number_column_name,
                table=config.destination_table_fqdn,
            )
        )
        if len(block_number_results) != 1:
            return AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.ERROR,
                description="No block results. Is this table empty?",
            )
        min_block_number = block_number_results[0].min_block_number
        max_block_number = block_number_results[0].max_block_number
        blocks_count = block_number_results[0].blocks_count
        # Add one to include the min block in the count
        expected_count = max_block_number - min_block_number + 1
        metadata = dict(
            min_block_number=min_block_number,
            max_block_number=max_block_number,
            blocks_count=blocks_count,
            expected_count=expected_count,
        )
        if min_block_number not in [0, 1]:
            return AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.WARN,
                description="Minimum block number is not 0 or 1 for a full scan",
                metadata=metadata,
            )

        return AssetCheckResult(
            passed=blocks_count == expected_count,
            severity=AssetCheckSeverity.WARN,
            description="Did not get the expected number of blocks",
            metadata=metadata,
        )

    return _block_number_check


def traces_checks(
    block_number_column_name: str = "block_number",
) -> CheckFactory[GoldskyConfig]:
    def check_factory(
        config: GoldskyConfig, asset: AssetsDefinition
    ) -> List[AssetChecksDefinition]:
        # TODO add a check to check traces exist for all transaction_ids
        return [block_number_check(block_number_column_name, config, asset)]

    return check_factory


def transactions_checks(
    block_number_column_name: str = "block_number",
) -> CheckFactory[GoldskyConfig]:
    def check_factory(config: GoldskyConfig, asset: AssetsDefinition):
        # TODO add a check to check ensure that transactions exist for all blocks
        return [block_number_check(block_number_column_name, config, asset)]

    return check_factory


def blocks_checks(
    block_number_column_name: str = "number",
) -> CheckFactory[GoldskyConfig]:
    def check_factory(config: GoldskyConfig, asset: AssetsDefinition):
        return [block_number_check(block_number_column_name, config, asset)]

    return check_factory
