import typing as t
from operator import methodcaller

import arrow
import pandas as pd
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
    RetryPolicy,
    define_asset_job,
    multi_asset,
)
from oso_dagster.cbt.cbt import CBTResource
from oso_dagster.config import DagsterConfig
from oso_dagster.dlt_sources.github_repos import (
    GithubClientConfig,
    GithubRepositoryResolver,
    GithubURLType,
    oss_directory_github_funding_resource,
    oss_directory_github_repositories_resource,
    oss_directory_github_sbom_relationships_resource,
    oss_directory_github_sbom_resource,
)
from oso_dagster.factories import dlt_factory
from oso_dagster.factories.common import AssetFactoryResponse
from oso_dagster.factories.jobs import discoverable_jobs
from oso_dagster.utils import (
    ChunkedResourceConfig,
    process_chunked_resource,
    secret_ref_arg,
)
from oso_dagster.utils.tags import add_tags
from ossdirectory import fetch_data
from ossdirectory.fetch import OSSDirectory

# NOTE: Since we are running on spot instances, we need to set a higher retry
# count to account for the fact that spot instances can be terminated at any time.
MAX_RETRY_COUNT = 25

K8S_CONFIG = {
    "merge_behavior": "SHALLOW",
    "container_config": {
        "resources": {
            "requests": {"cpu": "2000m", "memory": "3584Mi"},
            "limits": {"memory": "7168Mi"},
        },
    },
    "pod_spec_config": {
        "node_selector": {
            "pool_type": "spot",
        },
        "tolerations": [
            {
                "key": "pool_type",
                "operator": "Equal",
                "value": "spot",
                "effect": "NoSchedule",
            }
        ],
    },
}


common_tags: t.Dict[str, str] = {
    "opensource.observer/environment": "production",
    "opensource.observer/group": "ossd",
    "opensource.observer/type": "source",
    "dagster/concurrency_key": "ossd",
}

stable_tag = add_tags(common_tags, {"opensource.observer/source": "stable"})


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

    # FIXME: Address this when polar fixes missing columns
    # df = pl.from_dicts(getattr(data, output))
    df = pl.from_pandas(pd.DataFrame.from_records(getattr(data, output)))
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


def create_sbom_fetch_function(
    context: AssetExecutionContext,
    cbt: CBTResource,
    gh_token: str,
    max_sbom_age_days: int,
    table_name: str,
    data_type: str = "SBOMs",
) -> t.Callable[[], t.List[t.Tuple[str, str]]]:
    """
    Creates a fetch function for SBOM-related data that queries BigQuery to find
    repositories that need data fetched.

    Args:
        context: Dagster execution context
        cbt: CBT resource for BigQuery access
        gh_token: GitHub token for API access
        max_sbom_age_days: Maximum age in days before refetching data
        table_name: Name of the table to check for existing data
        data_type: Description of the data type for logging

    Returns:
        A function that returns a list of (owner, repo) tuples
    """

    def fetch_fn() -> t.List[t.Tuple[str, str]]:
        table_suffix = table_name.split(".")[-1]

        all_repositories_query = f"""
            WITH
              latest_{table_suffix} AS (
              SELECT
                artifact_namespace,
                artifact_name,
                MAX(snapshot_at) AS latest_snapshot
              FROM
                `{table_name}`
              GROUP BY
                artifact_namespace,
                artifact_name ),
              repos_needing_{table_suffix} AS (
              SELECT
                r.url,
                r.owner,
                r.name
              FROM
                `ossd.repositories` r
              LEFT JOIN
                latest_{table_suffix} s
              ON
                r.owner = s.artifact_namespace
                AND r.name = s.artifact_name
              WHERE
                LOWER(r.url) LIKE '%github.com%'
                AND (
                  s.latest_snapshot IS NULL
                  OR s.latest_snapshot < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {max_sbom_age_days} DAY) ) )
            SELECT
              DISTINCT url
            FROM
              repos_needing_{table_suffix};
        """

        config = GithubClientConfig(
            gh_token=gh_token,
        )

        gh = GithubRepositoryResolver.get_github_client(config)
        resolver = GithubRepositoryResolver(gh)

        client = cbt.get(context.log)

        all_repo_urls: t.Set[str] = {
            row["url"] for row in client.query_with_string(all_repositories_query)
        }

        clean_repos = [
            (repo.owner, repo.repository)
            for repo in (resolver.safe_parse_url(url) for url in all_repo_urls)
            if repo and repo.type == GithubURLType.REPOSITORY and repo.repository
        ]

        context.log.info(f"Fetching {data_type} for {len(clean_repos)} repositories")

        return clean_repos

    return fetch_fn


@multi_asset(
    outs={
        "projects": AssetOut(is_required=False, key_prefix="ossd", tags=stable_tag),
        "collections": AssetOut(is_required=False, key_prefix="ossd", tags=stable_tag),
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
    tags=dict(stable_tag.items()),
    op_tags={"dagster-k8s/config": K8S_CONFIG},
    retry_policy=RetryPolicy(max_retries=MAX_RETRY_COUNT),
)
def repositories(
    global_config: ResourceParam[DagsterConfig],
    context: AssetExecutionContext,
    projects_df: pl.DataFrame,
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    def fetch_fn() -> t.List[str]:
        config = GithubClientConfig(
            gh_token=gh_token,
        )

        gh = GithubRepositoryResolver.get_github_client(config)
        resolver = GithubRepositoryResolver(gh)

        urls = resolver.github_urls_from_df(projects_df)

        valid_urls = list(
            set(url for url in urls["url"] if resolver.safe_parse_url(url))
        )

        context.log.info(
            f"Fetching repositories for {len(valid_urls)} unique GitHub URLs"
        )

        return valid_urls

    return process_chunked_resource(
        ChunkedResourceConfig(
            fetch_data_fn=fetch_fn,
            resource=oss_directory_github_repositories_resource,
            to_serializable_fn=methodcaller("model_dump"),
            gcs_bucket_name=global_config.gcs_bucket,
            context=context,
        ),
        gh_token,
    )


@dlt_factory(
    key_prefix="ossd",
    deps=[AssetKey(["ossd", "repositories"])],
    tags=dict(add_tags(common_tags, {"opensource.observer/source": "sbom"}).items()),
    op_tags={"dagster-k8s/config": K8S_CONFIG},
    retry_policy=RetryPolicy(max_retries=MAX_RETRY_COUNT),
)
def sbom(
    global_config: ResourceParam[DagsterConfig],
    context: AssetExecutionContext,
    cbt: CBTResource,
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    max_sbom_age_days = context.get_tag("max-sbom-age-days") or "7"

    try:
        max_sbom_age_days = int(max_sbom_age_days)
    except ValueError:
        context.log.error(
            f"Invalid value for `max-sbom-age-days`: {max_sbom_age_days}. Using default value of 7 days"
        )
        max_sbom_age_days = 7

    fetch_fn = create_sbom_fetch_function(
        context=context,
        cbt=cbt,
        gh_token=gh_token,
        max_sbom_age_days=max_sbom_age_days,
        table_name="ossd.sbom",
        data_type="SBOMs",
    )

    return process_chunked_resource(
        ChunkedResourceConfig(
            fetch_data_fn=fetch_fn,
            resource=oss_directory_github_sbom_resource,
            to_serializable_fn=methodcaller("model_dump"),
            gcs_bucket_name=global_config.gcs_bucket,
            context=context,
        ),
        gh_token,
    )


@dlt_factory(
    key_prefix="ossd",
    deps=[AssetKey(["ossd", "repositories"])],
    tags=dict(add_tags(common_tags, {"opensource.observer/source": "sbom"}).items()),
    op_tags={"dagster-k8s/config": K8S_CONFIG},
    retry_policy=RetryPolicy(max_retries=MAX_RETRY_COUNT),
)
def sbom_relationships(
    global_config: ResourceParam[DagsterConfig],
    context: AssetExecutionContext,
    cbt: CBTResource,
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    max_sbom_age_days = context.get_tag("max-sbom-age-days") or "7"

    try:
        max_sbom_age_days = int(max_sbom_age_days)
    except ValueError:
        context.log.error(
            f"Invalid value for `max-sbom-age-days`: {max_sbom_age_days}. Using default value of 7 days"
        )
        max_sbom_age_days = 7

    fetch_fn = create_sbom_fetch_function(
        context=context,
        cbt=cbt,
        gh_token=gh_token,
        max_sbom_age_days=max_sbom_age_days,
        table_name="ossd.sbom",
        data_type="SBOM relationships",
    )

    return process_chunked_resource(
        ChunkedResourceConfig(
            fetch_data_fn=fetch_fn,
            resource=oss_directory_github_sbom_relationships_resource,
            to_serializable_fn=methodcaller("model_dump"),
            gcs_bucket_name=global_config.gcs_bucket,
            context=context,
        ),
        gh_token,
    )


@dlt_factory(
    key_prefix="ossd",
    tags=dict(add_tags(common_tags, {"opensource.observer/source": "sbom"}).items()),
    op_tags={"dagster-k8s/config": K8S_CONFIG},
    retry_policy=RetryPolicy(max_retries=MAX_RETRY_COUNT),
)
def funding(
    gh_token: str = secret_ref_arg(group_name="ossd", key="github_token"),
):
    yield oss_directory_github_funding_resource(
        "opensource-observer",
        "oss-funding",
        "data/funding_data.csv",
        gh_token=gh_token,
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
