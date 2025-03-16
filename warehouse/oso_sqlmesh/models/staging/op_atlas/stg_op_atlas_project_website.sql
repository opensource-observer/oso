MODEL (
  name oso.stg_op_atlas_project_website,
  dialect trino,
  kind FULL
);

SELECT
  @oso_id('OP_ATLAS', '', projects.id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
  LOWER(websites.value) AS artifact_source_id,
  'WWW' AS artifact_source,
  '' AS artifact_namespace,
  websites.value AS artifact_name,
  websites.value AS artifact_url,
  'WEBSITE' AS artifact_type
FROM @oso_source('bigquery.op_atlas.project__website') AS websites
INNER JOIN @oso_source('bigquery.op_atlas.project') AS projects
  ON websites._dlt_parent_id = projects._dlt_id
