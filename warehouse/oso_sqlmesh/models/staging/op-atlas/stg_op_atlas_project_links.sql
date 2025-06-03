MODEL (
  name oso.stg_op_atlas_project_links,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH cleaned_data AS (
  SELECT
    LOWER(project_id::VARCHAR) AS project_id,
    LOWER(url) AS url,
    updated_at
  FROM @oso_source('bigquery.op_atlas.project_links')
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, url ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  url AS artifact_source_id,
  'WWW' AS artifact_source,
  '' AS artifact_namespace,
  url AS artifact_name,
  url AS artifact_url,
  'WEBSITE' AS artifact_type
FROM latest_data
WHERE rn = 1