MODEL (
  name oso.stg_op_atlas_project_defillama,
  dialect trino,
  kind FULL
);

WITH manual_mappings AS (
  SELECT project_id, defillama_slug FROM (VALUES
    ('0xd4f0252e6ac2408099cd40d213fb6f42e8fa129b446d6e8da55e673598ef14c0', 'moonwell'),
    ('0xfd9f98de666c5b0a5ce96d4a4b8d4ceee9f8c2156734d57bf6c23d0cff183e90', 'kim-exchange')
  ) AS x (project_id, defillama_slug)
),

app_mappings_raw AS (
  SELECT DISTINCT
    LOWER(p.id::VARCHAR) AS project_id,
    LOWER(d.value) AS defillama_slug,
    p.updated_at
  FROM @oso_source('bigquery.op_atlas.project') AS p
  JOIN @oso_source('bigquery.op_atlas.project__defi_llama_slug') AS d
    ON d._dlt_parent_id = p._dlt_id
  WHERE p.id NOT IN (SELECT project_id FROM manual_mappings)
),

app_mappings AS (
  SELECT *
  FROM (
    SELECT 
      *,
      ROW_NUMBER() OVER (
        PARTITION BY project_id, defillama_slug
        ORDER BY updated_at DESC
      ) AS rn
    FROM app_mappings_raw
  ) ranked
  WHERE rn = 1
),

combined_mappings AS (
  SELECT 
    COALESCE(m.project_id, a.project_id) AS project_id,
    COALESCE(m.defillama_slug, a.defillama_slug) AS defillama_slug
  FROM app_mappings a
  FULL OUTER JOIN manual_mappings m 
    ON a.project_id = m.project_id
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  CONCAT('https://defillama.com/protocol/', defillama_slug) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  '' AS artifact_namespace,
  defillama_slug AS artifact_name,
  CONCAT('https://defillama.com/protocol/', defillama_slug) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM combined_mappings