MODEL (
  name oso.int_repositories,
  description 'All repositories',
  kind FULL
);

SELECT
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
FROM oso.int_artifacts_by_project AS artifacts
INNER JOIN oso.stg_ossd__current_repositories AS repos
  ON artifacts.artifact_source_id = repos.id::TEXT