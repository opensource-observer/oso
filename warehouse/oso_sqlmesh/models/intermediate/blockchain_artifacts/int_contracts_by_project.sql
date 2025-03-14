MODEL (
  name oso.int_contracts_by_project,
  kind FULL,
  partitioned_by "artifact_namespace",
  description "Combines directly associated contracts and derived contracts from factory deployments"
);

WITH base_contracts AS (
  SELECT DISTINCT
    project_id,
    artifact_source,
    artifact_name
  FROM oso.int_artifacts_by_project_all_sources
  WHERE
    artifact_type = 'CONTRACT'
), contracts_from_deployers AS (
  SELECT DISTINCT
    deployers.project_id,
    derived.chain AS artifact_source,
    derived.contract_address AS artifact_name
  FROM oso.int_derived_contracts AS derived
  INNER JOIN oso.int_deployers_by_project AS deployers
    ON derived.chain = deployers.artifact_source
    AND derived.originating_address = deployers.artifact_name
), direct_contracts AS (
  SELECT
    *
  FROM base_contracts
  UNION ALL
  SELECT
    *
  FROM contracts_from_deployers
), contracts_from_factories AS (
  SELECT DISTINCT
    contracts.project_id,
    contracts.artifact_source,
    factories.contract_address AS artifact_name
  FROM oso.int_factories AS factories
  INNER JOIN direct_contracts AS contracts
    ON factories.chain = contracts.artifact_source
    AND factories.factory_address = contracts.artifact_name
), all_contracts AS (
  SELECT
    *
  FROM direct_contracts
  UNION ALL
  SELECT
    *
  FROM contracts_from_factories
)
SELECT DISTINCT
  project_id,
  @oso_id(artifact_source, artifact_name) AS artifact_id,
  artifact_source,
  artifact_name AS artifact_source_id,
  '' AS artifact_namespace,
  artifact_name
FROM all_contracts