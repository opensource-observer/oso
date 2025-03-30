MODEL(
  name oso.int_superchain_s7_onchain_metrics_by_project,
  description 'S7 onchain metrics by project with various aggregations and filters',
  kind incremental_by_time_range(
   time_column sample_date,
   batch_size 90,
   batch_concurrency 1,
   lookback 7
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by DAY("sample_date"),
  grain(sample_date, chain, project_id, metric_name)
);

@DEF(direct_invocation_weight, 0.5);
@DEF(internal_invocation_weight, 0.5);

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
  LEFT OUTER JOIN oso.int_superchain_onchain_user_labels AS users
  ON e.from_artifact_id = users.artifact_id
  WHERE
    /* Currently no 4337-specific logic as these events are 
    already captured in the CONTRACT_INTERNAL_INVOCATION
    events and would need to be de-duped. */ 
    e.event_type IN (
      'CONTRACT_INVOCATION',
      'CONTRACT_INTERNAL_INVOCATION'
    )
    AND e.time BETWEEN @start_dt AND @end_dt
),

-- Calculate number of projects involved in internal invocations per transaction
internal_projects_per_tx AS (
  SELECT 
    transaction_hash,
    COUNT(DISTINCT project_id) as num_internal_projects
  FROM base_events
  WHERE event_type = 'CONTRACT_INTERNAL_INVOCATION'
  GROUP BY transaction_hash
),

-- Calculate weights for each event
weighted_events AS (
  SELECT
    e.*,
    COALESCE(i.num_internal_projects, 0) as num_internal_projects,
    CASE
      WHEN e.event_type = 'CONTRACT_INVOCATION' THEN
        CASE 
          -- No internal projects, get full weight
          WHEN COALESCE(i.num_internal_projects, 0) = 0 THEN 1.0
          -- Has internal projects, get 50%
          ELSE @direct_invocation_weight  
        END
      WHEN e.event_type = 'CONTRACT_INTERNAL_INVOCATION' THEN
        -- Split remaining 50% among internal projects
        @internal_invocation_weight / NULLIF(i.num_internal_projects, 0)
    END as transaction_weight
  FROM base_events e
  LEFT JOIN internal_projects_per_tx i
    ON e.transaction_hash = i.transaction_hash
),

-- Amortized transaction counts
amortized_transaction_count AS (
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'amortized_contract_invocations_monthly' AS metric_name,
    SUM(transaction_weight) AS amount
  FROM weighted_events
  GROUP BY 1, 2, 3
),

-- Transaction counts
transaction_count AS (
  SELECT
    project_id,
    chain,
    bucket_month AS sample_date,
    'contract_invocations_monthly' AS metric_name,
    COUNT(DISTINCT transaction_hash) AS amount
  FROM weighted_events
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
  FROM weighted_events AS e
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
defillama_tvl_events AS (
  SELECT
    dl.project_id,
    UPPER(dl.from_artifact_namespace) AS chain,
    DATE_TRUNC('DAY', dl.bucket_day::DATE) AS bucket_day,
    DATE_TRUNC('MONTH', dl.bucket_day::DATE) AS bucket_month,
    dl.amount
  FROM oso.int_events_daily_to_project__defillama_tvl AS dl
  WHERE
    dl.event_type = 'DEFILLAMA_TVL'
    AND dl.from_artifact_name = 'usd'
    AND dl.from_artifact_namespace IN (
      SELECT LOWER(chain)
      FROM oso.int_superchain_chain_names
    )
),

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
  FROM weighted_events
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
  FROM weighted_events
  GROUP BY 1, 2, 3
),

union_all_metrics AS (
  SELECT *
  FROM amortized_transaction_count
  UNION ALL
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
  sample_date::TIMESTAMP AS sample_date,
  metric_name::TEXT AS metric_name,
  amount::DOUBLE AS amount
FROM union_all_metrics