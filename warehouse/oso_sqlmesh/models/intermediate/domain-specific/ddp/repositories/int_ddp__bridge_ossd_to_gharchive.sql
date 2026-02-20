MODEL (
  name oso.int_ddp__bridge_ossd_to_gharchive,
  description 'Maps OSS_DIRECTORY GitHub repositories to their numeric GitHub repo IDs (gharchive_id) via artifact_source_id.',
  dialect trino,
  kind FULL,
  grain (project_id, gharchive_id),
  tags (
    "ddp",
    "entity_category=project"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  p.project_id,
  p.project_name,
  p.display_name AS project_display_name,
  CONCAT(a.artifact_namespace, '/', a.artifact_name) AS repo_name,
  TRY_CAST(a.artifact_source_id AS BIGINT) AS gharchive_id
FROM oso.projects_v1 AS p
JOIN oso.artifacts_by_project_v1 AS a
  ON p.project_id = a.project_id
WHERE
  a.artifact_source = 'GITHUB'
  AND p.project_source = 'OSS_DIRECTORY'
  AND a.artifact_source_id IS NOT NULL
  AND a.artifact_source_id != ''
