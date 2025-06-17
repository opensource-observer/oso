MODEL (
  name oso.int_artifacts_by_project_in_ossd_downstream,
  kind FULL,
  dialect trino,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH project_deployers AS (
  SELECT
    project_id,
    artifact_name
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type = 'DEPLOYER'
),

project_factories AS (
  SELECT
    project_id,
    artifact_name,
    artifact_source
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type = 'FACTORY'
),

contracts_from_deployers AS (
  SELECT
    project_deployers.project_id,
    derived_contracts.chain AS artifact_source,
    derived_contracts.contract_address AS artifact_name
  FROM oso.int_derived_contracts AS derived_contracts
  INNER JOIN project_deployers
    ON derived_contracts.originating_address = project_deployers.artifact_name
),

contracts_from_factories AS (
  SELECT
    project_factories.project_id,
    factories.chain AS artifact_source,
    factories.contract_address AS artifact_name
  FROM oso.int_factories AS factories
  INNER JOIN project_factories
    ON factories.factory_address = project_factories.artifact_name
    AND factories.chain = project_factories.artifact_source
),

all_contracts AS (
  SELECT
    project_id,
    artifact_source,
    artifact_name
  FROM contracts_from_deployers
  UNION ALL
  SELECT
    project_id,
    artifact_source,
    artifact_name
  FROM contracts_from_factories
)

SELECT DISTINCT
  project_id,
  @oso_entity_id(artifact_source, '', artifact_name) AS artifact_id,
  artifact_source,
  artifact_name AS artifact_source_id,
  '' AS artifact_namespace,
  artifact_name
FROM all_contracts