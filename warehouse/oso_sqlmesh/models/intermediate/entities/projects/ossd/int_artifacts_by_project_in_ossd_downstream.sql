MODEL (
  name oso.int_artifacts_by_project_in_ossd_downstream,
  description "Discovers all contracts downstream of project deployers and factories",
  kind FULL,
  dialect trino,
  partitioned_by (
    artifact_source,
    artifact_type
  ),
  grain (project_id, artifact_id),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Get all deployers for a project
WITH project_deployers AS (
  SELECT
    project_id,
    artifact_name
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type = 'DEPLOYER'
),

-- Get all factories for a project
project_factories AS (
  SELECT
    project_id,
    artifact_name,
    artifact_source
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type = 'FACTORY'
),

-- Get all contracts downstream of project deployers
contracts_from_deployers AS (
  SELECT DISTINCT
    pd.project_id,
    derived.chain AS artifact_source,
    derived.contract_address AS artifact_name
  FROM project_deployers AS pd
  JOIN oso.int_derived_contracts AS derived
    ON
      -- Direct deployments
      derived.originating_address = pd.artifact_name
      OR 
      -- Deployments through factories
      derived.factory_address IN (
        SELECT contract_address 
        FROM oso.int_derived_contracts 
        WHERE originating_address = pd.artifact_name
      )
),

-- Get all contracts downstream of project factories
contracts_from_factories AS (
  SELECT DISTINCT
    pf.project_id,
    derived.chain AS artifact_source,
    derived.contract_address AS artifact_name
  FROM project_factories AS pf
  JOIN oso.int_derived_contracts AS derived
    ON derived.factory_address = pf.artifact_name
    AND derived.chain = pf.artifact_source
)

SELECT DISTINCT
  project_id,
  @oso_entity_id(artifact_source, '', artifact_name) AS artifact_id,
  artifact_source,
  artifact_name AS artifact_source_id,
  '' AS artifact_namespace,
  artifact_name,
  'CONTRACT' AS artifact_type,
  artifact_name AS artifact_url
FROM (
  SELECT * FROM contracts_from_deployers
  UNION ALL
  SELECT * FROM contracts_from_factories
) all_contracts