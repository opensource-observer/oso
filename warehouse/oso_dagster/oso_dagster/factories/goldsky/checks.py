import os
from typing import List, Optional, Tuple

import arrow
import sqlglot as sql
from dagster import (
    AssetCheckExecutionContext,
    AssetCheckResult,
    AssetChecksDefinition,
    AssetCheckSeverity,
    AssetsDefinition,
    Config,
    asset_check,
)

from ...cbt import CBTResource, Transformation
from ...cbt.transforms import context_query_replace_source_tables, time_constrain_table
from ..common import AssetFactoryResponse
from .config import AdditionalAssetFactory, GoldskyConfig


def generated_asset_prefix(asset: AssetsDefinition):
    return "_".join(asset.key.path)


class BlockchainCheckConfig(Config):
    start: Optional[str] = None
    end: Optional[str] = None
    full_refresh: bool = False

    def get_range(self) -> Tuple[arrow.Arrow | None, arrow.Arrow | None]:
        now = arrow.now()
        if self.full_refresh:
            return (None, now.shift(days=-1))
        if self.start or self.end:
            start = arrow.get(self.start) if self.start is not None else None
            end = arrow.get(self.end) if self.end is not None else None
            return (start, end)
        # By default check the last 2 weeks of data
        return (now.shift(days=-15), now.shift(days=-1))


def traces_check(
    traces_transaction_hash_column_name: str,
    traces_block_timestamp_column_name: str,
    transactions_table_fqn: str,
    transactions_transaction_hash_column_name: str,
    transactions_block_timestamp_column_name: str,
    gs_config: GoldskyConfig,
    asset: AssetsDefinition,
):
    prefix = generated_asset_prefix(asset)

    @asset_check(name=f"{prefix}_traces_check", asset=asset)
    def _traces_check(
        context: AssetCheckExecutionContext,
        cbt: CBTResource,
        config: BlockchainCheckConfig,
    ):
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        start, end = config.get_range()
        transformations: List[Transformation] = [
            time_constrain_table(
                traces_block_timestamp_column_name,
                table_name="traces",
                start=start,
                end=end,
            ),
            time_constrain_table(
                transactions_block_timestamp_column_name,
                table_name="transactions",
                start=start,
                end=end,
            ),
            context_query_replace_source_tables(
                sql.to_table("traces"),
                sql.to_table(gs_config.destination_table_fqn, dialect="bigquery"),
            ),
            context_query_replace_source_tables(
                sql.to_table("transactions"),
                sql.to_table(transactions_table_fqn, dialect="bigquery"),
            ),
        ]

        block_number_results = list(
            c.hybrid_query(
                "traces_check.sql",
                transformations=transformations,
                traces_transaction_hash_column_name=traces_transaction_hash_column_name,
                transactions_transaction_hash_column_name=transactions_transaction_hash_column_name,
            )
        )
        if len(block_number_results) != 1:
            return AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.ERROR,
                description="No block results. Is this table empty?",
            )
        missing_transaction_hashes = block_number_results[0].missing_transaction_hashes
        # Add one to include the min block in the count
        metadata = dict(missing_transaction_hashes=missing_transaction_hashes)
        if missing_transaction_hashes != 0:
            return AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.WARN,
                description="Transactions are missing",
                metadata=metadata,
            )

        return AssetCheckResult(
            passed=missing_transaction_hashes == 0,
            severity=AssetCheckSeverity.WARN,
            description="Did not get the expected transactions",
            metadata=metadata,
        )

    return _traces_check


def transactions_check(
    transactions_block_hash_column_name: str,
    transactions_block_timestamp_column_name: str,
    blocks_table_fqn: str,
    blocks_block_hash_column_name: str,
    blocks_block_timestamp_column_name: str,
    gs_config: GoldskyConfig,
    asset: AssetsDefinition,
):
    prefix = generated_asset_prefix(asset)

    @asset_check(name=f"{prefix}_transactions_check", asset=asset)
    def _transactions_check(
        context: AssetCheckExecutionContext,
        cbt: CBTResource,
        config: BlockchainCheckConfig,
    ):
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        start, end = config.get_range()
        transformations: List[Transformation] = [
            time_constrain_table(
                transactions_block_timestamp_column_name,
                table_name="transactions",
                start=start,
                end=end,
            ),
            time_constrain_table(
                blocks_block_timestamp_column_name,
                table_name="blocks",
                start=start,
                end=end,
            ),
            context_query_replace_source_tables(
                sql.to_table("transactions"),
                sql.to_table(gs_config.destination_table_fqn, dialect="bigquery"),
            ),
            context_query_replace_source_tables(
                sql.to_table("blocks"),
                sql.to_table(blocks_table_fqn, dialect="bigquery"),
            ),
        ]

        block_number_results = list(
            c.hybrid_query(
                "transactions_check.sql",
                transformations=transformations,
                transactions_block_hash_column_name=transactions_block_hash_column_name,
                blocks_block_hash_column_name=blocks_block_hash_column_name,
            )
        )
        if len(block_number_results) != 1:
            return AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.ERROR,
                description="No block results. Is this table empty?",
            )
        missing_block_hashes = block_number_results[0].missing_block_hashes
        # Add one to include the min block in the count
        metadata = dict(missing_block_hashes=missing_block_hashes)
        return AssetCheckResult(
            passed=missing_block_hashes == 0,
            severity=AssetCheckSeverity.WARN,
            description="Did not get the expected number of blocks",
            metadata=metadata,
        )

    return _transactions_check


def missing_blocks_model(
    block_number_column_name: str,
    block_timestamp_column_name: str,
    gs_config: GoldskyConfig,
    asset: AssetsDefinition,
):
    prefix = generated_asset_prefix(asset)

    @asset_check(name=f"{prefix}_missing_blocks_model", asset=asset)
    def _missing_blocks_model(
        context: AssetCheckExecutionContext,
        cbt: CBTResource,
        config: BlockchainCheckConfig,
    ):
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        start, end = config.get_range()

        transformations: List[Transformation] = [
            time_constrain_table(
                block_timestamp_column_name,
                table_name="blocks",
                start=start,
                end=end,
            ),
            context_query_replace_source_tables(
                sql.to_table("blocks"),
                sql.to_table(gs_config.destination_table_fqn, dialect="bigquery"),
            ),
        ]

        try:
            c.hybrid_transform(
                "blocks_missing_block_numbers.sql",
                gs_config.destination_table_fqn,
                transformations=transformations,
                block_number_column_name=block_number_column_name,
            )
        except Exception:
            return AssetCheckResult(
                passed=False,
                severity=AssetCheckSeverity.WARN,
                description="Did not succeed to update the blocks missing",
            )

        return AssetCheckResult(
            passed=True,
            severity=AssetCheckSeverity.WARN,
            description="Successfully update missing block numbers",
        )

    return _missing_blocks_model


def block_number_check(
    block_number_column_name: str,
    block_timestamp_column_name: str,
    gs_config: GoldskyConfig,
    asset: AssetsDefinition,
) -> AssetChecksDefinition:
    prefix = generated_asset_prefix(asset)

    @asset_check(name=f"{prefix}_block_number_check", asset=asset)
    def _block_number_check(
        context: AssetCheckExecutionContext,
        cbt: CBTResource,
        config: BlockchainCheckConfig,
    ):
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        start, end = config.get_range()
        transformations: List[Transformation] = [
            time_constrain_table(
                block_timestamp_column_name,
                table_name="blocks",
                start=start,
                end=end,
            ),
            context_query_replace_source_tables(
                sql.to_table("blocks"),
                sql.to_table(gs_config.destination_table_fqn, dialect="bigquery"),
            ),
        ]

        block_number_results = list(
            c.hybrid_query(
                "block_number_check.sql",
                transformations=transformations,
                block_number_column_name=block_number_column_name,
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
        if config.full_refresh and min_block_number not in [0, 1]:
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
    transactions_table_fqn: str,
    traces_transaction_hash_column_name: str = "transaction_hash",
    traces_block_timestamp_column_name: str = "block_timestamp",
    transactions_transaction_hash_column_name: str = "hash",
    transactions_block_timestamp_column_name: str = "block_timestamp",
) -> AdditionalAssetFactory[GoldskyConfig]:
    def check_factory(config: GoldskyConfig, asset: AssetsDefinition):
        # TODO add a check to check traces exist for all transaction_ids
        return AssetFactoryResponse(
            [],
            checks=[
                traces_check(
                    traces_transaction_hash_column_name,
                    traces_block_timestamp_column_name,
                    transactions_table_fqn,
                    transactions_transaction_hash_column_name,
                    transactions_block_timestamp_column_name,
                    config,
                    asset,
                )
            ],
        )

    return check_factory


def transactions_checks(
    blocks_table_fqn: str,
    transactions_block_hash_column_name: str = "block_hash",
    transactions_block_timestamp_column_name: str = "block_timestamp",
    blocks_block_hash_column_name: str = "hash",
    blocks_block_timestamp_column_name: str = "timestamp",
) -> AdditionalAssetFactory[GoldskyConfig]:
    def check_factory(config: GoldskyConfig, asset: AssetsDefinition):
        # TODO add a check to check ensure that transactions exist for all blocks
        return AssetFactoryResponse(
            [],
            checks=[
                transactions_check(
                    transactions_block_hash_column_name,
                    transactions_block_timestamp_column_name,
                    blocks_table_fqn,
                    blocks_block_hash_column_name,
                    blocks_block_timestamp_column_name,
                    config,
                    asset,
                )
            ],
        )

    return check_factory


def blocks_checks(
    block_number_column_name: str = "number",
    block_timestamp_column_name: str = "timestamp",
) -> AdditionalAssetFactory[GoldskyConfig]:
    def check_factory(config: GoldskyConfig, asset: AssetsDefinition):
        return AssetFactoryResponse(
            [],
            checks=[
                block_number_check(
                    block_number_column_name, block_timestamp_column_name, config, asset
                )
            ],
        )

    return check_factory
