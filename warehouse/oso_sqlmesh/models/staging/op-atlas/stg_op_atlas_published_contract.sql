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
    LOWER(project_id::VARCHAR) AS project_id,
    LOWER(contract) AS contract_address,
    chain_id
  FROM @oso_source('bigquery.op_atlas.published_contract')
  WHERE revoked_at IS NULL
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