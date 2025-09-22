MODEL (
  name oso.int_chain_metrics_from_oso_contracts,
  description "Chain-level metrics from OSO contracts",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  dialect trino,
  grain (sample_date, chain, metric_name),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
    "incrementalmustdefinenogapsaudit",
  )
);

WITH contract_metrics AS (
  SELECT
    DATE_TRUNC('DAY', deployment_timestamp::DATE) AS sample_date,
    contract_namespace AS chain,
    'CONTRACTS_DEPLOYED' AS metric_name,
    APPROX_DISTINCT(contract_address) AS amount
  FROM oso.int_contracts_overview
  WHERE
    deployment_timestamp BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

deployer_metrics AS (
  SELECT
    DATE_TRUNC('DAY', deployment_timestamp::DATE) AS sample_date,
    contract_namespace AS chain,
    'ACTIVE_DEPLOYERS' AS metric_name,
    APPROX_DISTINCT(originating_address) AS amount
  FROM oso.int_contracts_overview
  WHERE
    deployment_timestamp BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

root_deployer_metrics AS (
  SELECT
    DATE_TRUNC('DAY', deployment_timestamp::DATE) AS sample_date,
    contract_namespace AS chain,
    'ACTIVE_ROOT_DEPLOYERS' AS metric_name,
    APPROX_DISTINCT(root_deployer_address) AS amount
  FROM oso.int_contracts_overview
  WHERE
    deployment_timestamp BETWEEN @start_dt AND @end_dt
  GROUP BY 1, 2
),

union_metrics AS (
  SELECT * FROM contract_metrics
  UNION ALL
  SELECT * FROM deployer_metrics
  UNION ALL
  SELECT * FROM root_deployer_metrics
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM union_metrics