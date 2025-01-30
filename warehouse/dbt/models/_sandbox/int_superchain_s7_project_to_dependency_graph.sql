{{
  config(
    materialized='table'
  )
}}


with eligible_onchain_repos as (
  select * from {{ ref('int_superchain_s7_onchain_builder_repositories') }}
),

all_dependencies as (
  select distinct
    sbom.project_id as dependent_project_id,
    sbom.artifact_id as dependent_artifact_id,
    sbom.package_github_project_id as dependency_project_id,
    sbom.package_github_artifact_id as dependency_artifact_id,
    sbom.package_artifact_name as dependency_name,
    sbom.package_artifact_source as dependency_source
  from {{ ref('int_sbom_artifacts') }} as sbom
  inner join eligible_onchain_repos
    on sbom.artifact_id = eligible_onchain_repos.repo_artifact_id
  where
    sbom.project_id != sbom.package_github_project_id
    and sbom.package_github_artifact_id is not null
),

devtool_repo_stats as (
  select
    project_id as devtooling_project_id,
    artifact_id as repo_artifact_id,
    artifact_namespace as dependency_repo_owner,
    artifact_name as dependency_repo_name,
    language as dependency_repo_language,
    created_at as dependency_repo_created_at,
    updated_at as dependency_repo_updated_at,
    star_count as dependency_repo_stars,
    fork_count as dependency_repo_forks
  from {{ ref('int_repositories') }}
),

releases as (
  select
    devtool_repo_stats.repo_artifact_id,
    max(events.time) as last_release_published
  from devtool_repo_stats
  inner join {{ ref('int_events__github') }} as events
    on devtool_repo_stats.repo_artifact_id = events.to_artifact_id
  where events.event_type = 'RELEASE_PUBLISHED'
  group by repo_artifact_id
)

select
  eligible_onchain_repos.sample_date,
  all_dependencies.dependent_project_id,
  all_dependencies.dependent_artifact_id,
  all_dependencies.dependency_project_id,
  all_dependencies.dependency_artifact_id,
  all_dependencies.dependency_name,
  all_dependencies.dependency_source,
  eligible_onchain_repos.project_transaction_count,
  eligible_onchain_repos.project_gas_fees,
  eligible_onchain_repos.project_user_count,
  devtool_repo_stats.dependency_repo_language,
  devtool_repo_stats.dependency_repo_created_at,
  devtool_repo_stats.dependency_repo_updated_at,
  releases.last_release_published
from all_dependencies
inner join eligible_onchain_repos
  on all_dependencies.dependent_artifact_id = eligible_onchain_repos.repo_artifact_id
inner join devtool_repo_stats
  on all_dependencies.dependency_artifact_id = devtool_repo_stats.repo_artifact_id
inner join releases
  on all_dependencies.dependency_artifact_id = releases.repo_artifact_id
