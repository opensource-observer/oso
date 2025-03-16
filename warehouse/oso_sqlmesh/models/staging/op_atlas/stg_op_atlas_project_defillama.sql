  MODEL (
  name oso.stg_op_atlas_project_defillama,
  dialect trino,
  kind FULL
);

WITH cleaned_data AS (
  SELECT
    LOWER(projects.id::VARCHAR) AS project_id,
    LOWER(defillama.value) AS defillama_slug,
    projects.updated_at AS updated_at
  FROM @oso_source('bigquery.op_atlas.project__defi_llama_slug') AS defillama
  INNER JOIN @oso_source('bigquery.op_atlas.project') AS projects
    ON defillama._dlt_parent_id = projects._dlt_id
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, defillama_slug ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
) 

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  CONCAT('https://defillama.com/protocol/', defillama_slug) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  '' AS artifact_namespace,
  defillama_slug AS artifact_name,
  CONCAT('https://defillama.com/protocol/', defillama_slug) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM latest_data
WHERE rn = 1