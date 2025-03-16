MODEL (
  name oso.stg_op_atlas_project_links,
  dialect trino,
  kind FULL
);

WITH latest_links AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, url ORDER BY updated_at DESC) AS rn
  FROM @oso_source('bigquery.op_atlas.project_links')
)
SELECT
  @oso_id('OP_ATLAS', '', project_id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
  LOWER(url) AS artifact_source_id,
  'WWW' AS artifact_source,
  '' AS artifact_namespace,
  url AS artifact_name,
  url AS artifact_url,
  'WEBSITE' AS artifact_type,
  name AS display_name,
  description,
  created_at,
  updated_at
FROM latest_links
WHERE
  rn = 1
