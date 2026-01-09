MODEL (
  name oso.int_artifacts_by_project_discovered,
  kind FULL,
  dialect trino,
  partitioned_by (
    artifact_source,
    artifact_type
  ),
  grain (project_id, artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  u.project_id,
  p.package_artifact_id AS artifact_id,
  p.package_artifact_name AS artifact_source_id,
  p.package_artifact_source AS artifact_source,
  'PACKAGE' AS artifact_type,
  p.package_artifact_namespace AS artifact_namespace,
  p.package_artifact_name AS artifact_name,
  p.package_artifact_url AS artifact_url
FROM oso.int_packages__current_maintainer_only AS p
JOIN oso.int_artifacts_by_project_all_unioned_not_distinct AS u
  ON p.package_owner_artifact_id = u.artifact_id