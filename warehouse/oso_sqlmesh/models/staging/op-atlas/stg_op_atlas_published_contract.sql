MODEL (
  name oso.stg_op_atlas_published_contract,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH latest_data AS (
  SELECT DISTINCT
    LOWER(project_id::TEXT) AS atlas_id,
    LOWER(contract::TEXT) AS contract_address,
    chain_id::INTEGER AS chain_id
  FROM @oso_source('bigquery.op_atlas.published_contract')
  WHERE revoked_at IS NULL
)

SELECT DISTINCT
  atlas_id,
  contract_address,
  chain_id
FROM latest_data