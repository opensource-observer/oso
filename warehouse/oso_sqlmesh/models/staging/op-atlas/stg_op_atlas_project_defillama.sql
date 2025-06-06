MODEL (
  name oso.stg_op_atlas_project_defillama,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH manual_mappings AS (
  SELECT project_id, defillama_slug FROM (VALUES
    ('0xd4f0252e6ac2408099cd40d213fb6f42e8fa129b446d6e8da55e673598ef14c0', 'moonwell-lending'), -- missing from app
    ('0xd4f0252e6ac2408099cd40d213fb6f42e8fa129b446d6e8da55e673598ef14c0', 'moonwell-vaults'), -- missing from app
    ('0xfd9f98de666c5b0a5ce96d4a4b8d4ceee9f8c2156734d57bf6c23d0cff183e90', 'kim-exchange'), -- missing from app
    ('0x96767e87a27cdb9798f40c3a6fd78e70da611afe53a5e45cbaafc50cae4ad0e7', 'sonus'), -- legacy parent protocol name
    ('0x7262ed9c020b3b41ac7ba405aab4ff37575f8b6f975ebed2e65554a08419f8f4', 'sablier-finance'), -- legacy parent protocol name
    ('0x9c691ba3012549259099205cc1a7ca4d09d9b7a24a1b7b821b52c7bf1c9b89f4', 'origin-defi') -- legacy parent protocol name
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
    project_id,
    defillama_slug
  FROM app_mappings
  UNION ALL
  SELECT
    project_id,
    defillama_slug
  FROM manual_mappings
)

SELECT DISTINCT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  CONCAT('https://defillama.com/protocol/', defillama_slug) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  '' AS artifact_namespace,
  defillama_slug AS artifact_name,
  CONCAT('https://defillama.com/protocol/', defillama_slug) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM combined_mappings