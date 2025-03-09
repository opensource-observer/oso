MODEL(
  name oso.int_superchain_s7_onchain_metrics_by_project,
  description 'S7 onchain metrics by project with various aggregations and filters',
  kind incremental_by_time_range(
   time_column sample_date,
   batch_size 90,
   batch_concurrency 1,
   lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by day("sample_date"),
  grain(sample_date, chain, project_id, metric_name),
  enabled false,
);

-- Get all events for projects in the measurement period
WITH base_events AS (
  SELECT
    e.project_id,
    DATE_TRUNC('DAY', e.time::DATE) AS bucket_day,
    DATE_TRUNC('MONTH', e.time::DATE) AS bucket_month,
    e.event_type,
    e.event_source AS chain,
    e.from_artifact_id,
    e.to_artifact_id,
    e.gas_fee,
    e.transaction_hash,
    COALESCE(users.is_farcaster_user, false) AS is_farcaster_user
  FROM oso.int_superchain_events_by_project AS e
  INNER JOIN oso.projects_by_collection_v1 AS pbc
    ON e.project_id = pbc.project_id
  LEFT OUTER JOIN oso.int_superchain_onchain_user_labels AS users
  ON e.from_artifact_id = users.artifact_id
  WHERE
    e.time BETWEEN @start_dt AND @end_dt
    -- AND pbc.project_namespace = 'S7P1'
    -- Currently no 4337-specific logic
    AND e.event_type IN (
      'CONTRACT_INVOCATION',
      'CONTRACT_INTERNAL_INVOCATION'
    )
),

defillama_tvl_events AS (
  SELECT
    dl.project_id,
    dl.event_source AS chain,
    DATE_TRUNC('DAY', dl.bucket_day::DATE) AS bucket_day,
    DATE_TRUNC('MONTH', dl.bucket_day::DATE) AS bucket_month,
    dl.amount
  FROM oso.int_events_daily__defillama_tvl AS dl
  INNER JOIN oso.projects_by_collection_v1 AS pbc
    ON dl.project_id = pbc.project_id
  WHERE
    dl.bucket_day BETWEEN @start_dt AND @end_dt
    -- AND pbc.project_namespace = 'S7P1'
    AND dl.event_type = 'DEFILLAMA_TVL'
),

-- Transaction counts
transaction_count AS (
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'contract_invocations_monthly' AS metric_name,
    COUNT(DISTINCT transaction_hash) AS amount
  FROM base_events
  GROUP BY 1, 2, 3
),

-- Gas fees
transaction_gas_fee AS (
  WITH project_event_types AS (
    -- First, identify which projects have direct CONTRACT_INVOCATION events
    SELECT DISTINCT project_id, chain
    FROM base_events
    WHERE event_type = 'CONTRACT_INVOCATION'
  )
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'gas_fees_monthly' AS metric_name,
    SUM(gas_fee) AS amount
  FROM base_events AS e
  WHERE (
    -- Include CONTRACT_INVOCATION events for all projects that have them
    event_type = 'CONTRACT_INVOCATION'
    OR
    -- Include CONTRACT_INTERNAL_INVOCATION only for projects that don't have direct invocations
    (event_type = 'CONTRACT_INTERNAL_INVOCATION' 
     AND NOT EXISTS (
       SELECT 1 
       FROM project_event_types AS pet 
       WHERE pet.project_id = e.project_id 
         AND pet.chain = e.chain
     ))
  )
  GROUP BY 1, 2, 3
),

-- Defillama TVL
defillama_tvl AS (
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'average_tvl_monthly' AS metric_name,
    AVG(amount) AS amount
  FROM defillama_tvl_events
  GROUP BY 1, 2, 3
),

-- Active Farcaster users
monthly_active_farcaster_users AS (
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'active_farcaster_users_monthly' AS metric_name,
    COUNT(DISTINCT from_artifact_id) AS amount
  FROM base_events
  WHERE is_farcaster_user = true
  GROUP BY 1, 2, 3
),

-- Active addresses
monthly_active_addresses AS (
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'active_addresses_monthly' AS metric_name,
    COUNT(DISTINCT from_artifact_id) AS amount
  FROM base_events
  GROUP BY 1, 2, 3
),

union_all_metrics AS (
  SELECT *
  FROM transaction_count
  UNION ALL
  SELECT *
  FROM transaction_gas_fee
  UNION ALL
  SELECT *
  FROM defillama_tvl
  UNION ALL
  SELECT *
  FROM monthly_active_farcaster_users
  UNION ALL
  SELECT *
  FROM monthly_active_addresses
)

SELECT
  project_id::TEXT AS project_id,
  chain::TEXT AS chain,
  sample_date::DATE AS sample_date,
  metric_name::TEXT AS metric_name,
  amount::DOUBLE AS amount
FROM union_all_metrics
