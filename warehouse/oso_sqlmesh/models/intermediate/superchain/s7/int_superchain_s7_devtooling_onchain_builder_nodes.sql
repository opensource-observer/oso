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
@DEF(measurement_date, DATE('2025-03-01'));

WITH eligible_builder_projects AS (
  SELECT
    repos.artifact_id,
    repos.artifact_namespace,
    repos.artifact_name,
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
),

aggregated_builder_metrics AS (
  SELECT
    artifact_id,
    artifact_namespace,
    artifact_name,
    
    MAX(CASE WHEN project_source = 'OSS_DIRECTORY' THEN project_id END) AS oso_project_id,
    
    COALESCE(
      ARRAY_AGG(DISTINCT project_name) FILTER (WHERE project_source = 'OP_ATLAS'),
      CAST(ARRAY[] AS ARRAY(VARCHAR))
    ) AS op_atlas_project_names,
    
    MAX(transaction_count) AS total_transaction_count,
    MAX(gas_fees) AS total_gas_fees,
    MAX(active_addresses_count) AS total_active_addresses_count
  FROM eligible_builder_projects
  GROUP BY
    artifact_id,
    artifact_namespace,
    artifact_name
)

SELECT
  @measurement_date AS sample_date,
  COALESCE(metrics.oso_project_id, artifacts.project_id) AS oso_project_id,
  metrics.artifact_id,
  metrics.artifact_namespace,
  metrics.op_atlas_project_names,
  metrics.total_transaction_count,
  metrics.total_gas_fees,
  metrics.total_active_addresses_count
FROM aggregated_builder_metrics AS metrics
JOIN oso.artifacts_by_project_v1 AS artifacts
  ON metrics.artifact_id = artifacts.artifact_id
WHERE artifacts.project_source = 'OSS_DIRECTORY'