with github_stats as (
  select
    to_artifact_id as artifact_id,
    MIN(time) as first_commit_time,
    MAX(time) as last_commit_time,
    COUNT(distinct TIMESTAMP_TRUNC(time, day)) as days_with_commits_count,
    COUNT(distinct from_artifact_id) as contributors_to_repo_count
  from {{ ref('int_events_with_artifact_id') }}
  where event_type = 'COMMIT_CODE'
  group by to_artifact_id
)

select
  int_ossd__repositories_by_project.project_id,
  int_ossd__repositories_by_project.artifact_id,
  int_ossd__repositories_by_project.owner as repo_owner,
  int_ossd__repositories_by_project.name as repo_name,
  int_ossd__repositories_by_project.is_fork,
  int_ossd__repositories_by_project.fork_count,
  int_ossd__repositories_by_project.star_count,
  github_stats.first_commit_time,
  github_stats.last_commit_time,
  github_stats.days_with_commits_count,
  github_stats.contributors_to_repo_count
from {{ ref('int_ossd__repositories_by_project') }}
left join github_stats
  on int_ossd__repositories_by_project.artifact_id = github_stats.artifact_id
