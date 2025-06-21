MODEL (
  name oso.int_repositories__ossd,
  description 'All repositories in OSSD',
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  repos.id AS artifact_source_id,
  artifact_fields.artifact_source,
  artifact_fields.artifact_namespace,
  artifact_fields.artifact_name,
  artifact_fields.artifact_url,
  artifact_fields.artifact_type,
  repos.node_id,
  repos.url,
  repos.name,
  repos.name_with_owner,
  repos.owner,
  'https://github.com/' || repos.owner AS owner_url,
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
FROM oso.stg_ossd__current_repositories AS repos
CROSS JOIN LATERAL @parse_github_repository_artifact(repos.url) AS artifact_fields