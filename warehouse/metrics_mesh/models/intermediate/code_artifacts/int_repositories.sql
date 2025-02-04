MODEL (
  name metrics.int_repositories,
  description 'All repositories',
  kind FULL,
);

select
  artifacts.project_id,
  artifacts.artifact_id,
  artifacts.artifact_source_id,
  artifacts.artifact_source,
  artifacts.artifact_namespace,
  artifacts.artifact_name,
  artifacts.artifact_url,
  repos.is_fork,
  repos.branch,
  repos.star_count,
  repos.watcher_count,
  repos.fork_count,
  repos.license_name,
  repos.license_spdx_id,
  repos.language,
  repos.created_at,
  repos.updated_at
from metrics.int_artifacts_in_ossd_by_project as artifacts
inner join @oso_source('bigquery.oso.stg_ossd__current_repositories') as repos
  on artifacts.artifact_source_id = CAST(repos.id as STRING)
