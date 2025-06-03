MODEL (
  name oso.int_github_users,
  description 'All GitHub users',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  artifact_source_id,
  artifact_id,
  artifact_namespace,
  artifact_name,
  'GIT_USER' AS artifact_type,
  'https://github.com/' || artifact_name AS artifact_url
FROM oso.int_first_last_commit_from_github_user
