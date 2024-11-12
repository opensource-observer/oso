{{ 
  config(
    materialized='table'
  ) 
}}

with repo_artifact as (
  select
    'GITHUB' as artifact_source,
    is_fork,
    fork_count,
    star_count,
    license_spdx_id,
    language,
    watcher_count,
    created_at,
    updated_at,
    CAST(id as STRING) as artifact_source_id,
    LOWER(owner) as artifact_namespace,
    LOWER(name) as artifact_name
  from {{ ref('stg_ossd__current_repositories') }}
),

repo_snapshot as (
  select distinct
    {{ oso_id("a.artifact_source", "a.artifact_source_id") }} as `artifact_id`,
    artifact_namespace,
    artifact_name,
    license_spdx_id,
    language,
    is_fork,
    fork_count,
    star_count,
    watcher_count,
    created_at,
    updated_at
  from repo_artifact as a
),

repo_stats as (
  select
    project_id,
    to_artifact_id as artifact_id,
    MIN(time) as first_commit_time,
    MAX(time) as last_commit_time,
    COUNT(distinct TIMESTAMP_TRUNC(time, day)) as days_with_commits_count,
    COUNT(distinct from_artifact_id) as contributors_to_repo_count,
    SUM(amount) as commit_count
  from {{ ref('int_events_to_project') }}
  where event_type = 'COMMIT_CODE'
  group by
    project_id,
    to_artifact_id
),

artifacts_project as (
  select distinct
    project_id,
    artifact_id,
    artifact_namespace,
    artifact_name,
    artifact_source,
    artifact_type
  from {{ ref('int_artifacts_in_ossd_by_project') }}
  where
    artifact_source = 'GITHUB'
    and artifact_type = 'REPOSITORY'
)

select distinct
  artifacts_project.project_id,
  artifacts_project.artifact_id,
  artifacts_project.artifact_namespace,
  artifacts_project.artifact_name,
  artifacts_project.artifact_source,
  repo_snapshot.is_fork,
  repo_snapshot.fork_count,
  repo_snapshot.star_count,
  repo_snapshot.watcher_count,
  repo_snapshot.language,
  repo_snapshot.license_spdx_id,
  repo_snapshot.created_at,
  repo_snapshot.updated_at,
  repo_stats.first_commit_time,
  repo_stats.last_commit_time,
  repo_stats.days_with_commits_count,
  repo_stats.contributors_to_repo_count,
  repo_stats.commit_count
from artifacts_project
left join repo_snapshot
  on artifacts_project.artifact_id = repo_snapshot.artifact_id
left join repo_stats
  on artifacts_project.artifact_id = repo_stats.artifact_id
