MODEL (
  name oso.stg_op_atlas_project_deployer,
  dialect trino,
  kind FULL
);

WITH latest_deployers AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY project_id, chain_id, deployer_address ORDER BY updated_at DESC) AS rn
  FROM @oso_source('bigquery.op_atlas.project_contract')
)
SELECT
  @oso_id('OP_ATLAS', project_id) AS project_id, /* Translating op-atlas project_id to OSO project_id */
  LOWER(deployer_address) AS artifact_source_id,
  @chain_id_to_chain_name(chain_id) AS artifact_source,
  NULL::VARCHAR AS artifact_namespace,
  deployer_address AS artifact_name,
  NULL::VARCHAR AS artifact_url,
  'DEPLOYER' AS artifact_type
FROM latest_deployers
WHERE
  rn = 1