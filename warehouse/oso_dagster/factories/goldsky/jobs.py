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

from ...cbt import CBTResource, Transformation
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

        missing_blocks_model_name = f"{gs_config.project_id}.{gs_config.destination_dataset_name}.{gs_config.destination_table_name}_missing_block_numbers"

        c.hybrid_transform(
            "blocks_missing_block_numbers.sql",
            missing_blocks_model_name,
            transformations=transformations,
            block_number_column_name=block_number_column_name,
        )

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
