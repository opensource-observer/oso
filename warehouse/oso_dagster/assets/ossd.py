import typing as t

import arrow
import polars as pl
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    AssetSelection,
    Config,
    JsonMetadataValue,
    Output,
    ResourceParam,
    define_asset_job,
    multi_asset,
)
from oso_dagster.cbt.cbt import CBTResource
from oso_dagster.config import DagsterConfig
from oso_dagster.dlt_sources.github_repos import (
    oss_directory_github_repositories_resource,
    oss_directory_github_sbom_resource,
)
from oso_dagster.factories import dlt_factory
from oso_dagster.factories.common import AssetFactoryResponse
from oso_dagster.factories.jobs import discoverable_jobs
from oso_dagster.utils import secret_ref_arg
from ossdirectory import fetch_data
from ossdirectory.fetch import OSSDirectory

common_tags: t.Dict[str, str] = {
    "opensource.observer/environment": "production",
    "opensource.observer/group": "ossd",
    "opensource.observer/type": "source",
    "opensource.observer/source": "core",
    "dagster/concurrency_key": "ossd",
}


class OSSDirectoryConfig(Config):
    # By default, the oss-directory asset doesn't write anything if there aren't
    # any changes from the previous materialization. This happens by comparing
    # the sha of the current fetch_data and the sha stored in the metadata of
    # the last materialization
    force_write: bool = False


def oss_directory_to_dataframe(output: str, data: t.Optional[OSSDirectory] = None):
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
                repo_meta = t.cast(JsonMetadataValue, repo_meta)
                repo_meta_dict = t.cast(dict, repo_meta.data)
                context.log.debug(
                    {
                        "message": "repo_meta",
                        "repo_meta": repo_meta_dict,
                    }
                )
                # The previous sha for this asset and the current sha match. No
                # need to update anything.

                # FIXME in the future we should skip already materialized shas
                # if possible. For now we cannot, see:
                # https://github.com/dagster-io/dagster/discussions/19403
                if repo_meta_dict.get("sha", "") == data.meta.sha:
                    context.log.warn(f"no changes for {output}. Materializing anyway")
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
    global_config: ResourceParam[DagsterConfig],
    projects_df: pl.DataFrame,
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    yield oss_directory_github_repositories_resource(
        projects_df, gh_token, http_cache=global_config.http_cache
    )


@dlt_factory(
    key_prefix="ossd",
    deps=[AssetKey(["ossd", "repositories"])],
    tags=common_tags,
)
def sbom(
    global_config: ResourceParam[DagsterConfig],
    context: AssetExecutionContext,
    cbt: CBTResource,
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    all_repositories_query = """
        SELECT
        DISTINCT url
        FROM
        `ossd.repositories`
        WHERE
        LOWER(url) LIKE '%github.com%';
    """

    client = cbt.get(context.log)

    all_repo_urls: t.List[str] = [
        row["url"] for row in client.query_with_string(all_repositories_query)
    ]

    context.log.info(f"Fecthing SBOMs for {len(all_repo_urls)} repositories")

    yield oss_directory_github_sbom_resource(
        all_repo_urls, gh_token, http_cache=global_config.http_cache
    )


@discoverable_jobs(dependencies=[repositories])
def ossd_jobs(dependencies: t.List[AssetFactoryResponse]):
    repositories = t.cast(AssetsDefinition, list(dependencies[0].assets)[0])
    return [
        define_asset_job(
            name="oss_directory_sync",
            selection=AssetSelection.assets(projects_and_collections)
            | AssetSelection.assets(repositories),
        )
    ]
