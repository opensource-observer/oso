MODEL (
  name oso.stg_op_atlas_project_defillama,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT DISTINCT
    LOWER(p.id::TEXT) AS atlas_id,
    LOWER(d.value) AS defillama_slug,
    p.updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project') AS p
  INNER JOIN @oso_source('bigquery.op_atlas.project__defi_llama_slug') AS d
    ON d._dlt_parent_id = p._dlt_id
),

latest_data AS (
  SELECT
    atlas_id,
    defillama_slug,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, defillama_slug ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  defillama_slug,
  updated_at
FROM latest_data
WHERE rn = 1