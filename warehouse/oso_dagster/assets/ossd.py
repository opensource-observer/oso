from typing import cast

from dagster import (
    multi_asset,
    Output,
    AssetOut,
    AssetExecutionContext,
    JsonMetadataValue,
    Config,
)
from ossdirectory import fetch_data
import polars as pl
import arrow


class OSSDirectoryConfig(Config):
    force: bool = False


@multi_asset(
    outs={
        "projects": AssetOut(is_required=False, key_prefix="ossd"),
        "collections": AssetOut(is_required=False, key_prefix="ossd"),
    },
    can_subset=True,
)
def ossdirectory_repo(context: AssetExecutionContext, config: OSSDirectoryConfig):

    data = fetch_data()

    if not data.meta:
        raise Exception("ossdirectory repository metadata is required")

    for output in context.op_execution_context.selected_output_names:
        asset_key = context.asset_key_for_output(output)
        latest_materialization = context.instance.get_latest_materialization_event(
            asset_key=asset_key
        )
        if (
            latest_materialization
            and latest_materialization.asset_materialization
            and not config.force
        ):
            repo_meta = latest_materialization.asset_materialization.metadata.get(
                "repo_meta", {}
            )
            if repo_meta:
                repo_meta = cast(JsonMetadataValue, repo_meta)
                repo_meta_dict = cast(dict, repo_meta.data)
                context.log.debug(
                    {
                        "message": "repo_meta",
                        "repo_meta": repo_meta_dict,
                    }
                )
                if repo_meta_dict.get("sha", "") == data.meta.sha:
                    context.log.info(f"no changes for {output}")
                    continue
        context.log.debug(data.meta.committed_datetime)
        context.log.debug(type(data.meta.committed_datetime))
        committed_dt = data.meta.committed_datetime

        df = pl.from_dicts(getattr(data, output))
        df = df.with_columns(
            sha=pl.lit(bytes.fromhex(data.meta.sha)),
            committed_time=pl.datetime(
                committed_dt.year,
                committed_dt.month,
                committed_dt.day,
                committed_dt.hour,
                committed_dt.minute,
                committed_dt.second,
            ),
        )

        # Add sync time and commit sha to the dataframe
        yield Output(
            df,
            output,
            metadata={
                "repo_meta": {
                    "sha": data.meta.sha,
                    "committed": arrow.get(data.meta.committed_datetime).isoformat(),
                    "authored": arrow.get(data.meta.authored_datetime).isoformat(),
                }
            },
        )
