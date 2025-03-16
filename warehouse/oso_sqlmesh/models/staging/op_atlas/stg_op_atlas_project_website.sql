MODEL (
  name oso.stg_op_atlas_project_website,
  dialect trino,
  kind FULL
);

WITH cleaned_data AS (
  SELECT
    LOWER(projects.id::VARCHAR) AS project_id,
    LOWER(websites.value) AS website,
    projects.updated_at AS updated_at
  FROM @oso_source('bigquery.op_atlas.project__website') AS websites
  INNER JOIN @oso_source('bigquery.op_atlas.project') AS projects
    ON websites._dlt_parent_id = projects._dlt_id
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, website ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  website AS artifact_source_id,
  'WWW' AS artifact_source,
  '' AS artifact_namespace,
  website AS artifact_name,
  website AS artifact_url,
  'WEBSITE' AS artifact_type
FROM latest_data
WHERE rn = 1
