MODEL (
  name oso.stg_op_atlas_project_contract,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH source_data_raw AS (
  SELECT
    LOWER(pc.project_id::TEXT) AS atlas_id,
    LOWER(pc.contract_address) AS contract_address,
    LOWER(pc.deployer_address) AS deployer_address,
    pc.chain_id::INTEGER AS chain_id,
    pc.updated_at::TIMESTAMP AS updated_at
  FROM @oso_source('bigquery.op_atlas.project_contract') AS pc
  WHERE pc.contract_address IS NOT NULL AND pc.chain_id IS NOT NULL
),

latest_data AS (
  SELECT
    atlas_id,
    contract_address,
    deployer_address,
    chain_id,
    updated_at,
    ROW_NUMBER() OVER (PARTITION BY atlas_id, chain_id, contract_address ORDER BY updated_at DESC) AS rn
  FROM source_data_raw
)

SELECT
  atlas_id,
  contract_address,
  deployer_address,
  chain_id,
  updated_at
FROM latest_data
WHERE rn = 1