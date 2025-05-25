MODEL (
  name oso.int_github_repositories,
  description 'All GitHub repositories',
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
  MIN(first_commit_time) AS first_commit_time,
  MAX(last_commit_time) AS last_commit_time
FROM oso.int_first_last_commit_to_github_repository
GROUP BY
  artifact_source_id,
  artifact_id,
  artifact_namespace,
  artifact_name