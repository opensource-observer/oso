MODEL (
  name oso.stg_op_atlas_project_contract,
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH cleaned_data AS (
  SELECT
    LOWER(project_id::VARCHAR) AS project_id,
    LOWER(contract_address) AS contract_address,
    chain_id,
    updated_at
  FROM @oso_source('bigquery.op_atlas.project_contract')
),

latest_data AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, chain_id, contract_address ORDER BY updated_at DESC) AS rn
  FROM cleaned_data
)

SELECT
  @oso_entity_id('OP_ATLAS', '', project_id) AS project_id,
  contract_address AS artifact_source_id,
  @chain_id_to_chain_name(chain_id) AS artifact_source,
  '' AS artifact_namespace,
  contract_address AS artifact_name,
  contract_address AS artifact_url,
  'CONTRACT' AS artifact_type
FROM latest_data
WHERE rn = 1