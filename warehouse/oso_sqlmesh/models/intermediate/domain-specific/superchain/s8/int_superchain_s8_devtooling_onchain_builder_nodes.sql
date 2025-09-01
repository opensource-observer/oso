MODEL (
  name oso.int_superchain_s8_devtooling_onchain_builder_nodes,
  description "Identifies projects in Atlas and OSS Directory with active repos (TypeScript, Solidity, Rust, Vyper) that have ≥0.1 ETH in Superchain gas fees over a trailing 180-day window, producing monthly snapshots re-keyed to OSS Directory for use in Retro Funding S8 Devtooling eligibility.",
  dialect trino,
  kind full,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

@DEF(gas_fees_threshold, 0.1);

-- Generate monthly measurement periods for S8
WITH measurement_dates AS (
  SELECT
    last_day_of_month(d) AS measurement_date,
    date_trunc('month', d) AS sample_date
  FROM UNNEST(
    SEQUENCE(DATE '2025-08-01', DATE '2026-01-01', INTERVAL '1' MONTH)
  ) AS t(d)
),

-- Create a cartesian product of all relevant projects and measurement periods
project_measurement_dates AS (
  SELECT
    p.project_id,
    md.measurement_date,
    md.sample_date
  FROM oso.projects_v1 AS p
  CROSS JOIN measurement_dates AS md
  WHERE p.project_source IN ('OSS_DIRECTORY', 'OP_ATLAS')
),

-- Get all metric IDs for gas fees, contract invocations, and TVL on Superchain chains
metrics AS (
  SELECT DISTINCT
    m.metric_id,
    m.metric_name
  FROM oso.metrics_v0 AS m
  WHERE (
    m.metric_name LIKE '%_gas_fees_monthly'
    OR m.metric_name LIKE '%_contract_invocations_monthly'
    OR m.metric_name LIKE '%_defillama_tvl_monthly'
    OR m.metric_name LIKE '%_active_addresses_aggregation_monthly'
  )
    AND EXISTS (
      SELECT 1
      FROM oso.int_superchain_chain_names AS c
      WHERE
        m.metric_name = CONCAT(c.chain, '_gas_fees_monthly')
        OR m.metric_name = CONCAT(c.chain, '_contract_invocations_monthly')
        OR m.metric_name = CONCAT(c.chain, '_defillama_tvl_monthly')
        OR m.metric_name = CONCAT(c.chain, '_active_addresses_aggregation_monthly')
    )
),

-- Calculate metrics for each project over a 180-day trailing window
project_metrics AS (
  SELECT
    pmd.project_id,
    pmd.sample_date,
    SUM(CASE WHEN m.metric_name LIKE '%_gas_fees_monthly' THEN tm.amount ELSE 0 END) AS gas_fees,
    SUM(CASE WHEN m.metric_name LIKE '%_contract_invocations_monthly' THEN tm.amount ELSE 0 END) AS contract_invocations,
    SUM(CASE WHEN m.metric_name LIKE '%_defillama_tvl_monthly' THEN tm.amount ELSE NULL END) AS defillama_tvl,
    SUM(CASE WHEN m.metric_name LIKE '%_active_addresses_aggregation_monthly' THEN tm.amount ELSE NULL END) AS active_addresses
  FROM project_measurement_dates AS pmd
  JOIN oso.timeseries_metrics_by_project_v0 AS tm
    ON tm.project_id = pmd.project_id
   AND tm.sample_date BETWEEN pmd.measurement_date - INTERVAL '180' DAY AND pmd.measurement_date
  JOIN metrics AS m ON tm.metric_id = m.metric_id
  GROUP BY 1,2
),

-- Get all relevant repos linked to projects in OSS Directory
ossd_repos AS (
  SELECT
    abp.project_id,
    r.artifact_id,
    r.artifact_namespace,
    r.artifact_name,
    r.updated_at,
    r.language
  FROM oso.artifacts_by_project_v1 AS abp
  JOIN oso.int_repositories__ossd AS r
    ON r.artifact_id = abp.artifact_id
  WHERE abp.project_source = 'OSS_DIRECTORY'
    AND abp.artifact_source = 'GITHUB'
    AND r.language IN ('TypeScript', 'Solidity', 'Rust', 'Vyper')
    AND r.artifact_namespace != 'ethereum-optimism'
),

-- Assign metrics to eligible repos at each measurement period
eligible_repo_months AS (
  SELECT DISTINCT
    pm.sample_date,
    orp.project_id,
    orp.artifact_id,
    orp.artifact_namespace,
    orp.artifact_name,
    pm.gas_fees,
    pm.contract_invocations,
    pm.defillama_tvl,
    pm.active_addresses,
    orp.language,
    orp.updated_at
  FROM project_metrics AS pm
  JOIN ossd_repos AS orp
    ON orp.project_id = pm.project_id
  WHERE pm.gas_fees >= @gas_fees_threshold
),

-- Determine the best matching OP Atlas project (if it exists)
atlas_mappings AS (
  SELECT
    p2p.ossd_project_id,
    max_by(p.atlas_id, p.updated_at) AS op_atlas_id
  FROM oso.int_projects_to_projects AS p2p
  JOIN oso.stg_op_atlas_project AS p
    ON p2p.external_project_name = p.atlas_id
  WHERE p2p.external_project_source = 'OP_ATLAS'
    AND shared_artifact_type IN ('DEPLOYER', 'REPOSITORY', 'DEFILLAMA_PROTOCOL')
  GROUP BY 1
)

SELECT
  e.sample_date,
  e.project_id,
  e.artifact_id AS repo_artifact_id,
  e.artifact_namespace AS repo_artifact_namespace,
  e.artifact_name AS repo_artifact_name,
  e.updated_at,
  e.language,
  am.op_atlas_id AS op_atlas_project_name,
  e.gas_fees AS total_gas_fees,
  e.contract_invocations AS total_transaction_count,
  e.active_addresses AS total_active_addresses,
  e.defillama_tvl AS average_defillama_tvl
FROM eligible_repo_months AS e
LEFT JOIN atlas_mappings AS am
  ON e.project_id = am.ossd_project_id