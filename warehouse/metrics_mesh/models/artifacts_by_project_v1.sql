/* Mirrors the artifacts_by_project_v1 table in the source database. This is */ /* important for situations like trino and bigquery connections. As trino has no */ /* ways to optimize queries to bigquery since it's using the storage api */
MODEL (
  name metrics.artifacts_by_project_v1,
  kind FULL
);

SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM @oso_source('artifacts_by_project_v1')