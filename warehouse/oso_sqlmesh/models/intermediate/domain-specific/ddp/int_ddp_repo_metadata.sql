MODEL (
  name oso.int_ddp_repo_metadata,
  description "Developer Data Program repositories enriched with ecosystem membership (Ethereum, EVM L1/L2, Solana) and repository metadata from OSSD",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

-- Get the most recent repository metadata from OSSD
WITH ossd AS (
  SELECT
    artifact_id,
    MAX_BY(artifact_namespace, updated_at) AS artifact_namespace,
    MAX_BY(artifact_name, updated_at) AS artifact_name,
    MAX_BY(artifact_url, updated_at) AS artifact_url,
    MAX_BY(is_fork, updated_at) AS is_fork,
    MAX_BY(star_count, updated_at) AS star_count,
    MAX_BY(fork_count, updated_at) AS fork_count,
    MAX_BY(language, updated_at) AS language,
    MIN(created_at) AS created_at,
    MAX(updated_at) AS updated_at
  FROM oso.int_repositories__ossd
  GROUP BY artifact_id
),

-- Filter to relevant crypto ecosystem projects and get artifact metadata
ec_artifacts AS (
  SELECT DISTINCT
    artifact_id,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM oso.int_artifacts_by_project_in_crypto_ecosystems
  WHERE project_namespace = 'eco'
    AND project_name IN (
      'ethereum',
      'evm_compatible_layer_1s',
      'evm_compatible_layer_2s',
      'ethereum_virtual_machine_stack',
      'solana'
    )
),

ec_projects AS (
  SELECT
    artifact_id,
    project_name
  FROM oso.int_artifacts_by_project_in_crypto_ecosystems
  WHERE project_namespace = 'eco'
    AND project_name IN (
      'ethereum',
      'evm_compatible_layer_1s',
      'evm_compatible_layer_2s',
      'ethereum_virtual_machine_stack',
      'solana'
    )
),

-- Pivot ecosystem memberships into boolean flags
ec_pivot AS (
  SELECT
    artifact_id,
    CAST(SUM(1) FILTER (WHERE project_name = 'ethereum') > 0 AS BOOLEAN) AS is_ethereum,
    CAST(SUM(1) FILTER (WHERE project_name = 'evm_compatible_layer_1s') > 0 AS BOOLEAN) AS is_evm_l1,
    CAST(SUM(1) FILTER (WHERE project_name = 'evm_compatible_layer_2s') > 0 AS BOOLEAN) AS is_evm_l2,
    CAST(SUM(1) FILTER (WHERE project_name = 'ethereum_virtual_machine_stack') > 0 AS BOOLEAN) AS is_evm_stack,
    CAST(SUM(1) FILTER (WHERE project_name = 'solana') > 0 AS BOOLEAN) AS is_solana,
    COUNT(DISTINCT project_name) AS ecosystem_count
  FROM ec_projects
  GROUP BY artifact_id
),

-- Union all artifact IDs from both sources
all_artifact_ids AS (
  SELECT artifact_id FROM ossd
  UNION
  SELECT artifact_id FROM ec_artifacts
)

SELECT
  a.artifact_id,
  -- Prefer OSSD metadata, fall back to crypto ecosystems metadata
  COALESCE(o.artifact_namespace, e.artifact_namespace) AS artifact_namespace,
  COALESCE(o.artifact_name, e.artifact_name) AS artifact_name,
  COALESCE(o.artifact_url, e.artifact_url) AS artifact_url,
  -- Repository metadata (only available from OSSD)
  o.is_fork,
  o.star_count,
  o.fork_count,
  o.language,
  o.created_at,
  o.updated_at,
  -- Ecosystem membership flags
  p.is_ethereum,
  p.is_evm_l1,
  p.is_evm_l2,
  p.is_evm_stack,
  p.is_solana,
  p.ecosystem_count
FROM all_artifact_ids AS a
LEFT JOIN ossd AS o
  ON a.artifact_id = o.artifact_id
LEFT JOIN ec_artifacts AS e
  ON a.artifact_id = e.artifact_id
LEFT JOIN ec_pivot AS p
  ON a.artifact_id = p.artifact_id