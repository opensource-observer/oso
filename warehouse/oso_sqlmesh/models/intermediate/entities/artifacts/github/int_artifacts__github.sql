MODEL (
  name oso.int_artifacts__github,
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
  'REPOSITORY' AS artifact_type,
  'https://github.com/' || artifact_namespace || '/' || artifact_name
    AS artifact_url
FROM oso.int_first_last_commit_to_github_repository
GROUP BY
  artifact_source_id,
  artifact_id,
  artifact_namespace,
  artifact_name