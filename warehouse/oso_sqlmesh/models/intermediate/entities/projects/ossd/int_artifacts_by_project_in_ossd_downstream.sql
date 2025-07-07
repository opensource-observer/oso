MODEL (
  name oso.int_artifacts_by_project_in_ossd_downstream,
  description "Discovers all contracts downstream of project deployers and factories",
  kind FULL,
  dialect trino,
  partitioned_by "artifact_source",
  grain (project_id, artifact_id),
  tags (
    'entity_type=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH project_deployers AS (
  SELECT
    project_id,
    artifact_name AS deployer_address
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type = 'DEPLOYER'
),

project_contracts AS (
  SELECT
    project_id,
    artifact_name AS contract_address,
    artifact_source AS chain
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type IN ('FACTORY', 'CONTRACT')
),

first_level_contracts AS (
  SELECT
    pd.project_id,    
    dc.contract_address,
    dc.chain
  FROM oso.int_derived_contracts AS dc
  JOIN project_deployers AS pd
    ON pd.deployer_address = dc.originating_address
),

all_contracts AS (
  SELECT
    project_id,
    contract_address,
    chain
  FROM first_level_contracts
  UNION ALL
  SELECT
    project_id,
    contract_address,
    chain
  FROM project_contracts
),

second_level_contracts AS (
  SELECT
    ac.project_id,
    dc.contract_address,
    dc.chain
  FROM oso.int_derived_contracts AS dc
  JOIN all_contracts AS ac
    ON ac.contract_address = dc.factory_address
    AND dc.chain = ac.chain
),

union_all_contracts AS (
  SELECT * FROM first_level_contracts
  UNION ALL
  SELECT * FROM second_level_contracts
)

SELECT DISTINCT
  project_id,
  @oso_entity_id(chain, '', contract_address) AS artifact_id,
  chain AS artifact_source,
  contract_address AS artifact_source_id,
  '' AS artifact_namespace,
  contract_address AS artifact_name,
  'CONTRACT' AS artifact_type,
  contract_address AS artifact_url
FROM union_all_contracts