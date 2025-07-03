MODEL (
  name oso.repositories_v0,
  kind FULL,
  tags (
    'export',
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  is_fork,
  branch,
  star_count,
  watcher_count,
  fork_count,
  license_name,
  license_spdx_id,
  "language",
  created_at,
  updated_at
FROM oso.int_repositories__ossd