MODEL (
  name metrics.stg_op_atlas_project_contract,
  dialect trino,
  kind FULL,
);

select
  -- Translating op-atlas project_id to OSO project_id
  @oso_id('OP_ATLAS', project_id) as project_id,
  id as artifact_source_id,
  @chain_id_to_chain_name(chain_id) as artifact_source,
  NULL as artifact_namespace,
  contract_address as artifact_name,
  NULL as artifact_url,
  'CONTRACT' as artifact_type,
  --created_at,
  --updated_at,
  --chain_id,
  --deployer_address,
  --contract_address,
  --deployment_hash,
  --verification_proof
from @oso_source('bigquery.op_atlas.project_contract')