with repo_artifact as (
  select
    'GITHUB' as artifact_source,
    is_fork,
    fork_count,
    star_count,
    license_spdx_id,
    watcher_count,
    CAST(id as STRING) as artifact_source_id,
    LOWER(owner) as artifact_namespace,
    LOWER(name) as artifact_name
  from {{ ref('stg_ossd__current_repositories') }}
),

repo_snapshot as (
  select
    {{ oso_id("a.artifact_source", "a.artifact_source_id") }} as `artifact_id`,
    artifact_namespace,
    artifact_name,
    license_spdx_id,
    is_fork,
    fork_count,
    star_count,
    watcher_count
  from repo_artifact as a
),

repo_stats as (
  select
    project_id,
    to_artifact_id as artifact_id,
    MIN(time) as first_commit_time,
    MAX(time) as last_commit_time,
    COUNT(distinct TIMESTAMP_TRUNC(time, day)) as days_with_commits_count,
    COUNT(distinct from_artifact_id) as contributors_to_repo_count
  from {{ ref('int_events_to_project') }}
  where event_type = 'COMMIT_CODE'
  group by
    project_id,
    to_artifact_id
)


select
  int_artifacts_by_project.project_id,
  int_artifacts_by_project.artifact_id,
  int_artifacts_by_project.artifact_namespace,
  int_artifacts_by_project.artifact_name,
  repo_snapshot.is_fork,
  repo_snapshot.fork_count,
  repo_snapshot.star_count,
  repo_snapshot.watcher_count,
  repo_snapshot.license_spdx_id,
  repo_stats.first_commit_time,
  repo_stats.last_commit_time,
  repo_stats.days_with_commits_count,
  repo_stats.contributors_to_repo_count
from {{ ref('int_artifacts_by_project') }}
left join repo_snapshot
  on int_artifacts_by_project.artifact_id = repo_snapshot.artifact_id
left join repo_stats
  on int_artifacts_by_project.artifact_id = repo_stats.artifact_id
where
  int_artifacts_by_project.artifact_source = 'GITHUB'
  and UPPER(int_artifacts_by_project.artifact_type) = 'REPOSITORY'
