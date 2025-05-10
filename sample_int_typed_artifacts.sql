MODEL (
  name oso.int_typed_artifacts,
  description "Consolidated model for all artifact types with a type column",
  kind FULL,
  dialect trino,
  grain (artifact_id, artifact_type),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

/*
  This model consolidates different artifact types (deployers, contracts, bridges)
  into a single model with a type column. It enriches the raw artifacts with
  type-specific attributes and relationships.
  
  Benefits:
  - Single model for all artifact types
  - Common processing logic
  - Easier to add new artifact types
  - Reduced circular dependencies
*/

WITH 
-- Get base artifacts from raw_artifacts
base_artifacts AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    data_source,
    last_updated_at
  FROM oso.int_raw_artifacts
),

-- Enrich contract artifacts with deployment information
contract_artifacts AS (
  SELECT
    base.artifact_id,
    base.artifact_source_id,
    base.artifact_source,
    base.artifact_namespace,
    base.artifact_name,
    base.artifact_url,
    'CONTRACT' AS artifact_type,
    base.project_id,
    base.data_source,
    base.last_updated_at,
    deployments.deployment_timestamp,
    deployments.deployer_address,
    deployments.factory_address,
    deployments.create_type,
    deployments.is_proxy
  FROM base_artifacts AS base
  LEFT JOIN oso.int_contract_deployments AS deployments
    ON base.artifact_source = deployments.chain
    AND base.artifact_name = deployments.contract_address
  WHERE base.artifact_type = 'CONTRACT'
),

-- Enrich deployer artifacts
deployer_artifacts AS (
  SELECT
    base.artifact_id,
    base.artifact_source_id,
    base.artifact_source,
    base.artifact_namespace,
    base.artifact_name,
    base.artifact_url,
    'DEPLOYER' AS artifact_type,
    base.project_id,
    base.data_source,
    base.last_updated_at,
    NULL AS deployment_timestamp,
    NULL AS deployer_address,
    NULL AS factory_address,
    NULL AS create_type,
    FALSE AS is_proxy
  FROM base_artifacts AS base
  WHERE base.artifact_type = 'DEPLOYER'
),

-- Enrich bridge artifacts with chain information
bridge_artifacts AS (
  SELECT
    base.artifact_id,
    base.artifact_source_id,
    base.artifact_source,
    base.artifact_namespace,
    base.artifact_name,
    base.artifact_url,
    'BRIDGE' AS artifact_type,
    base.project_id,
    base.data_source,
    base.last_updated_at,
    NULL AS deployment_timestamp,
    NULL AS deployer_address,
    NULL AS factory_address,
    NULL AS create_type,
    FALSE AS is_proxy,
    chains.is_superchain
  FROM base_artifacts AS base
  LEFT JOIN oso.int_chain_references AS chains
    ON base.artifact_source = chains.chain
  WHERE base.artifact_type = 'BRIDGE'
),

-- Combine all artifact types
all_typed_artifacts AS (
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    data_source,
    last_updated_at,
    deployment_timestamp,
    deployer_address,
    factory_address,
    create_type,
    is_proxy,
    NULL AS is_superchain
  FROM contract_artifacts
  
  UNION ALL
  
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    data_source,
    last_updated_at,
    deployment_timestamp,
    deployer_address,
    factory_address,
    create_type,
    is_proxy,
    NULL AS is_superchain
  FROM deployer_artifacts
  
  UNION ALL
  
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    data_source,
    last_updated_at,
    deployment_timestamp,
    deployer_address,
    factory_address,
    create_type,
    is_proxy,
    is_superchain
  FROM bridge_artifacts
  
  UNION ALL
  
  -- Include other artifact types without type-specific enrichment
  SELECT
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type,
    project_id,
    data_source,
    last_updated_at,
    NULL AS deployment_timestamp,
    NULL AS deployer_address,
    NULL AS factory_address,
    NULL AS create_type,
    FALSE AS is_proxy,
    NULL AS is_superchain
  FROM base_artifacts
  WHERE artifact_type NOT IN ('CONTRACT', 'DEPLOYER', 'BRIDGE')
)

-- Final output with standardized schema
SELECT
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  project_id,
  data_source,
  last_updated_at,
  deployment_timestamp,
  deployer_address,
  factory_address,
  create_type,
  is_proxy,
  is_superchain
FROM all_typed_artifacts
