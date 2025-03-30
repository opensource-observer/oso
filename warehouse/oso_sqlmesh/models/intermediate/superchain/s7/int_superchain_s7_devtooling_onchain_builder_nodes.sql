/*
  TODO: Need to pull the sample_date for future versions of this model
*/

MODEL (
  name oso.int_superchain_s7_devtooling_onchain_builder_nodes,
  description "Identifies onchain builder nodes for the S7 devtooling round",
  dialect trino,
  kind full,
);

@DEF(gas_fees_threshold, 0.1);
@DEF(measurement_date, DATE('2025-02-28'));

WITH eligible_builder_projects AS (
  SELECT
    repos.artifact_id,
    repos.artifact_namespace,
    repos.artifact_name,
    repos.updated_at,
    repos.language,
    eligibility.project_id,
    projects.project_name,
    projects.project_source,
    eligibility.transaction_count,
    eligibility.gas_fees,
    eligibility.active_addresses_count
  FROM oso.int_repositories AS repos
  LEFT JOIN oso.int_superchain_s7_onchain_builder_eligibility AS eligibility
    ON repos.project_id = eligibility.project_id
  JOIN oso.projects_v1 AS projects
    ON eligibility.project_id = projects.project_id
  WHERE
    eligibility.gas_fees >= @gas_fees_threshold
    AND eligibility.sample_date = @measurement_date
    AND repos.language IN ('TypeScript', 'Solidity', 'Rust', 'Vyper')
    AND repos.artifact_namespace != 'ethereum-optimism'
),

aggregated_builder_metrics AS (
  SELECT
    artifact_id,
    artifact_namespace,
    artifact_name,
    updated_at,
    language,
    MAX(CASE WHEN project_source = 'OSS_DIRECTORY' THEN project_id END)
      AS oso_project_id,
    MAX(CASE WHEN project_source = 'OP_ATLAS' THEN project_name END)
      AS op_atlas_project_name,
    MAX(transaction_count) AS total_transaction_count,
    MAX(gas_fees) AS total_gas_fees,
    MAX(active_addresses_count) AS total_active_addresses_count
  FROM eligible_builder_projects
  GROUP BY
    artifact_id,
    artifact_namespace,
    artifact_name,
    updated_at,
    language
)

SELECT
  @measurement_date AS sample_date,
  COALESCE(metrics.oso_project_id, artifacts.project_id) AS project_id,
  metrics.artifact_id as repo_artifact_id,
  metrics.artifact_namespace as repo_artifact_namespace,
  metrics.artifact_name as repo_artifact_name,
  metrics.updated_at,
  metrics.language,
  metrics.op_atlas_project_name,
  metrics.total_transaction_count,
  metrics.total_gas_fees,
  metrics.total_active_addresses_count
FROM aggregated_builder_metrics AS metrics
JOIN oso.artifacts_by_project_v1 AS artifacts
  ON metrics.artifact_id = artifacts.artifact_id
WHERE artifacts.project_source = 'OSS_DIRECTORY'
