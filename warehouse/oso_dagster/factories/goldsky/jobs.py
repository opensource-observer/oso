import os
from typing import List, Optional, Tuple

from .config import GoldskyConfig
from dagster import (
    AssetsDefinition,
    OpExecutionContext,
    Config,
    op,
    job,
)
import arrow
import sqlglot as sql

from ...cbt import CBTResource, Transformation, UpdateStrategy
from ...cbt.transforms import time_constrain_table, context_query_replace_source_tables


def generated_asset_prefix(asset: AssetsDefinition):
    return "_".join(asset.key.path)


class MissingBlocksConfig(Config):
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


def blocks_missing_block_number_model(
    block_number_column_name: str,
    block_timestamp_column_name: str,
    gs_config: GoldskyConfig,
    asset: AssetsDefinition,
):
    prefix = generated_asset_prefix(asset)

    @op(name=f"{prefix}_blocks_missing_block_number_model_op")
    def op_missing_blocks_model(
        context: OpExecutionContext,
        cbt: CBTResource,
        config: MissingBlocksConfig,
    ) -> None:
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        start, end = config.get_range()

        # Sadly, the query we run for this is not something bigquery can do with
        # GENERATE_ARRAY for more than a million or so values so we need to
        # split this up. Arbitrarily, we run this for ten days at a time until
        # it's completed. This allows us to support chains that produce a block
        # every second.
        if start is None:
            # If the start is none then we're doing a full refresh. But we need
            # to set the starting place in order for us to handle separating the
            # queries for every month.
            partitions_table = f"{gs_config.project_id}.{gs_config.destination_dataset_name}.INFORMATION_SCHEMA.PARTITIONS"
            context.log.debug(f"querying {partitions_table}")
            response = c.hybrid_query(
                "partitions_range.sql",
                partitions_table=partitions_table,
                table_name=gs_config.destination_table_name,
            )
            rows = list(response)
            if len(rows) == 0:
                raise Exception(
                    f"no partitions found for {gs_config.destination_table_fqn}"
                )
            start = arrow.get(rows[0].min_partition_timestamp)
            context.log.debug(f"determined start of full_refresh {start}")

        count = 0
        # The maximum number of days we analyze
        max_days_interval = 10
        # We shift one day less than the days we analyze to ensure we get any
        # missing block numbers between days
        shift_interval = 9
        while start < end:
            section_end = start.shift(days=max_days_interval)
            if section_end > end:
                section_end = end
            transformations: List[Transformation] = [
                time_constrain_table(
                    block_timestamp_column_name,
                    table_name="blocks",
                    start=start,
                    end=section_end,
                ),
                context_query_replace_source_tables(
                    sql.to_table("blocks"),
                    sql.to_table(gs_config.destination_table_fqn, dialect="bigquery"),
                ),
            ]

            missing_blocks_model_name = f"{gs_config.project_id}.{gs_config.destination_dataset_name}.{gs_config.destination_table_name}_missing_block_numbers"

            update_strategy = UpdateStrategy.MERGE
            if config.full_refresh and count == 0:
                update_strategy = UpdateStrategy.REPLACE

            c.hybrid_transform(
                "blocks_missing_block_numbers.sql",
                missing_blocks_model_name,
                transformations=transformations,
                block_number_column_name=block_number_column_name,
                unique_column="block_number",
                update_strategy=update_strategy,
            )
            count += 1
            start = start.shift(days=shift_interval)

    @job(name=f"{prefix}_blocks_missing_block_number_model_job")
    def job_missing_blocks_model():
        op_missing_blocks_model()

    return job_missing_blocks_model


def blocks_additional_jobs(
    block_number_column_name: str = "number",
    block_timestamp_column_name: str = "timestamp",
):
    def _wrapped(gs_config: GoldskyConfig, generated_asset: AssetsDefinition):
        return [
            blocks_missing_block_number_model(
                block_number_column_name,
                block_timestamp_column_name,
                gs_config,
                generated_asset,
            )
        ]

    return _wrapped


def transactions_missing_block_number_model(
    *,
    blocks_table_fqn: str,
    blocks_block_number_column_name: str,
    blocks_block_timestamp_column_name: str,
    blocks_block_hash_column_name: str,
    blocks_transaction_count_column_name: str,
    transactions_block_timestamp_column_name: str,
    transactions_block_hash_column_name: str,
    gs_config: GoldskyConfig,
    asset: AssetsDefinition,
):
    prefix = generated_asset_prefix(asset)

    @op(name=f"{prefix}_transactions_missing_block_number_model_op")
    def op_missing_blocks_model(
        context: OpExecutionContext,
        cbt: CBTResource,
        config: MissingBlocksConfig,
    ) -> None:
        c = cbt.get(context.log)
        c.add_search_paths(
            [os.path.join(os.path.abspath(os.path.dirname(__file__)), "queries")]
        )

        start, end = config.get_range()

        if start is None:
            # If the start is none then we're doing a full refresh. But we need
            # to set the starting position for queries
            partitions_table = f"{gs_config.project_id}.{gs_config.destination_dataset_name}.INFORMATION_SCHEMA.PARTITIONS"
            context.log.debug(f"querying {partitions_table}")
            response = c.hybrid_query(
                "partitions_range.sql",
                partitions_table=partitions_table,
                table_name=gs_config.destination_table_name,
            )
            rows = list(response)
            if len(rows) == 0:
                raise Exception(
                    f"no partitions found for {gs_config.destination_table_fqn}"
                )
            start = arrow.get(rows[0].min_partition_timestamp)
            context.log.debug(f"determined start of full_refresh {start}")

        count = 0
        max_days_interval = 1
        # we run this on a day to day basis to potentially reduce the size of
        # bytes processed as it's always only a single partition in each of the
        # tables
        shift_interval = 1
        while start < end:
            section_end = start.shift(days=max_days_interval)
            if section_end > end:
                section_end = end
            transformations: List[Transformation] = [
                time_constrain_table(
                    blocks_block_timestamp_column_name,
                    table_name="blocks",
                    start=start,
                    end=section_end,
                ),
                time_constrain_table(
                    transactions_block_timestamp_column_name,
                    table_name="transactions",
                    start=start,
                    end=section_end,
                ),
                context_query_replace_source_tables(
                    sql.to_table("blocks"),
                    sql.to_table(blocks_table_fqn, dialect="bigquery"),
                ),
                context_query_replace_source_tables(
                    sql.to_table("transactions"),
                    sql.to_table(gs_config.destination_table_fqn, dialect="bigquery"),
                ),
            ]

            missing_blocks_model_name = f"{gs_config.project_id}.{gs_config.destination_dataset_name}.{gs_config.destination_table_name}_missing_block_numbers"

            update_strategy = UpdateStrategy.MERGE
            if config.full_refresh and count == 0:
                update_strategy = UpdateStrategy.REPLACE

            c.hybrid_transform(
                "transactions_missing_block_numbers.sql",
                missing_blocks_model_name,
                transformations=transformations,
                blocks_block_number_column_name=blocks_block_number_column_name,
                blocks_block_hash_column_name=blocks_block_hash_column_name,
                blocks_transaction_count_column_name=blocks_transaction_count_column_name,
                transactions_block_hash_column_name=transactions_block_hash_column_name,
                unique_column="block_number",
                update_strategy=update_strategy,
            )
            count += 1
            start = start.shift(days=shift_interval)

    @job(name=f"{prefix}_transactions_missing_block_number_model_job")
    def job_missing_blocks_model():
        op_missing_blocks_model()

    return job_missing_blocks_model


def transactions_additional_jobs(
    *,
    blocks_table_fqn: str,
    blocks_block_number_column_name: str = "number",
    blocks_block_timestamp_column_name: str = "timestamp",
    blocks_block_hash_column_name: str = "hash",
    blocks_transaction_count_column_name: str = "transaction_count",
    transactions_block_timestamp_column_name: str = "block_timestamp",
    transactions_block_hash_column_name: str = "block_hash",
):
    def _wrapped(gs_config: GoldskyConfig, generated_asset: AssetsDefinition):
        return [
            transactions_missing_block_number_model(
                blocks_table_fqn=blocks_table_fqn,
                gs_config=gs_config,
                asset=generated_asset,
                blocks_block_number_column_name=blocks_block_number_column_name,
                blocks_block_timestamp_column_name=blocks_block_timestamp_column_name,
                blocks_block_hash_column_name=blocks_block_hash_column_name,
                blocks_transaction_count_column_name=blocks_transaction_count_column_name,
                transactions_block_timestamp_column_name=transactions_block_timestamp_column_name,
                transactions_block_hash_column_name=transactions_block_hash_column_name,
            )
        ]

    return _wrapped
