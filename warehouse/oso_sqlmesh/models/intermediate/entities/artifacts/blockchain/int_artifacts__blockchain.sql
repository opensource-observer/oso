MODEL(
  name oso.int_artifacts__blockchain,
  description 'All blockchain artifacts',
  dialect trino,
  kind FULL,
  partitioned_by ("artifact_source", "artifact_type"),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH deployers AS (
  SELECT DISTINCT
    UPPER(chain) AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN create_type = 'create' THEN root_deployer_address
      ELSE originating_address END
    AS artifact_name,
    'DEPLOYER' AS artifact_type
  FROM oso.int_contracts_root_deployers
),

contracts AS (
  SELECT DISTINCT
    UPPER(chain) AS artifact_source,
    '' AS artifact_namespace,
    LOWER(contract_address) AS artifact_name,
    'CONTRACT' AS artifact_type
  FROM oso.int_contracts_root_deployers
),

factories AS (
  SELECT DISTINCT
    UPPER(chain) AS artifact_source,
    '' AS artifact_namespace,
    LOWER(factory_address) AS artifact_name,
    'FACTORY' AS artifact_type
  FROM oso.int_factories
),

eoas AS (
  SELECT DISTINCT
    UPPER(chain) AS artifact_source,
    '' AS artifact_namespace,
    LOWER(address) AS artifact_name,
    'EOA' AS artifact_type
  FROM oso.int_addresses__labeled_eoas
),

bridges AS (
  SELECT DISTINCT
    UPPER(chain) AS artifact_source,
    '' AS artifact_namespace,
    LOWER(address) AS artifact_name,
    'BRIDGE' AS artifact_type
  FROM oso.int_addresses__bridges
),

operators_4337 AS (
  SELECT DISTINCT
    UPPER(chain) AS artifact_source,
    '' AS artifact_namespace,
    LOWER(address) AS artifact_name,
    '4337_OPERATOR' AS artifact_type
  FROM oso.int_addresses__4337_operators
),

all_artifacts AS (
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_type
  FROM deployers
  UNION ALL
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_type
  FROM contracts
  UNION ALL
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_type
  FROM factories
  UNION ALL
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_type
  FROM eoas
  UNION ALL
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_type
  FROM bridges
  UNION ALL
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_type
  FROM operators_4337
)

SELECT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS artifact_id,
  artifact_name AS artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_type,
  artifact_name AS artifact_url
FROM all_artifacts