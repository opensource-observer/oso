from typing import cast, Optional, Dict

from dagster import (
    multi_asset,
    Output,
    AssetOut,
    AssetExecutionContext,
    JsonMetadataValue,
    Config,
    AssetIn,
)
from ossdirectory import fetch_data
from ossdirectory.fetch import OSSDirectory
import polars as pl
import arrow

from oso_dagster.dlt_sources.github_repos import (
    oss_directory_github_repositories_resource,
)
from oso_dagster.factories import dlt_factory
from oso_dagster.utils import secret_ref_arg

common_tags: Dict[str, str] = {
    "opensource.observer/environment": "production",
    "opensource.observer/group": "ossd",
    "opensource.observer/type": "source",
}


class OSSDirectoryConfig(Config):
    # By default, the oss-directory asset doesn't write anything if there aren't
    # any changes from the previous materialization. This happens by comparing
    # the sha of the current fetch_data and the sha stored in the metadata of
    # the last materialization
    force_write: bool = False


def oss_directory_to_dataframe(output: str, data: Optional[OSSDirectory] = None):
    if not data:
        data = fetch_data()
    assert data.meta is not None
    committed_dt = data.meta.committed_datetime

    df = pl.from_dicts(getattr(data, output))
    # Add sync time and commit sha to the dataframe
    df = df.with_columns(
        sha=pl.lit(bytes.fromhex(data.meta.sha)),
        # We need to instantiate the datetime here using this pl.datetime
        # constructor due to an issue with the datetime that's returned from
        # ossdirectory that has a timezone type that seems to be
        # incompatible with polars.
        committed_time=pl.datetime(
            committed_dt.year,
            committed_dt.month,
            committed_dt.day,
            committed_dt.hour,
            committed_dt.minute,
            committed_dt.second,
        ),
    )
    return df


@multi_asset(
    outs={
        "projects": AssetOut(is_required=False, key_prefix="ossd", tags=common_tags),
        "collections": AssetOut(is_required=False, key_prefix="ossd", tags=common_tags),
    },
    compute_kind="dataframe",
    can_subset=True,
)
def projects_and_collections(
    context: AssetExecutionContext, config: OSSDirectoryConfig
):
    """Materializes both the projects/collections from the oss-directory repo
    into separate dataframe assets.
    """
    data = fetch_data()

    if not data.meta:
        raise Exception("ossdirectory repository metadata is required")

    for output in context.op_execution_context.selected_output_names:
        asset_key = context.asset_key_for_output(output)
        latest_materialization = context.instance.get_latest_materialization_event(
            asset_key=asset_key
        )

        # Check if there's a previous materialization. We can choose not to add
        # any data to the database
        if (
            latest_materialization
            and latest_materialization.asset_materialization
            and not config.force_write
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
                # The previous sha for this asset and the current sha match. No
                # need to update anything
                if repo_meta_dict.get("sha", "") == data.meta.sha:
                    context.log.info(f"no changes for {output}")
                    continue
        df = oss_directory_to_dataframe(output, data)

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


project_key = projects_and_collections.keys_by_output_name["projects"]


@dlt_factory(
    key_prefix="ossd",
    ins={"projects_df": AssetIn(project_key)},
    tags=common_tags,
)
def repositories(
    projects_df: pl.DataFrame,
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    yield oss_directory_github_repositories_resource(projects_df, gh_token)
