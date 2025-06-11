MODEL(
  name oso.int_superchain_s7_onchain_metrics_by_project,
  description 'S7 onchain metrics by project with various aggregations and filters',
  kind full,
  dialect trino,
  partitioned_by DAY("sample_date"),
  grain(sample_date, chain, project_id, metric_name),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


WITH all_events AS (
  SELECT
    events.project_id,
    DATE_TRUNC('MONTH', events.time::DATE) AS sample_date,
    events.event_type,
    events.event_source AS chain,
    events.from_artifact_id,
    events.gas_fee,
    events.transaction_hash,
    events.event_weight,
    COALESCE(users.is_farcaster_user, false) AS is_farcaster_user
  FROM oso.int_superchain_s7_onchain_builder_events AS events
  LEFT JOIN oso.int_superchain_onchain_user_labels AS users
    ON events.from_artifact_id = users.artifact_id
),

grouped_events AS (
  SELECT
    sample_date,
    project_id,
    chain,
    event_type,
    COUNT(*) AS count_events,
    SUM(gas_fee) AS gas_fee,
  FROM all_events
  GROUP BY 1, 2, 3, 4
),

-- Amortized transaction counts
amortized_transaction_count AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'amortized_contract_invocations_monthly' AS metric_name,
    SUM(event_weight) AS amount
  FROM all_events
  GROUP BY 1, 2, 3
),

-- Standard transaction counts
transaction_count AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'transactions_monthly' AS metric_name,
    SUM(count_events) AS amount
  FROM grouped_events
  WHERE event_type = 'CONTRACT_INVOCATION'
  GROUP BY 1, 2, 3
),

-- Internal transaction counts
internal_transaction_count AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'internal_transactions_monthly' AS metric_name,
    SUM(count_events) AS amount
  FROM grouped_events
  WHERE event_type != 'CONTRACT_INVOCATION'
  GROUP BY 1, 2, 3
),

-- Transactions and internal invocations
contract_invocations_count AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'contract_invocations_monthly' AS metric_name,
    SUM(count_events) AS amount
  FROM grouped_events
  GROUP BY 1, 2, 3
),

-- AA-related userop counts
aa_userop_count AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'account_abstraction_userops_monthly' AS metric_name,
    SUM(count_events) AS amount
  FROM grouped_events
  WHERE event_type IN (
    'CONTRACT_INVOCATION_VIA_USEROP',
    'CONTRACT_INVOCATION_VIA_PAYMASTER',
    'CONTRACT_INVOCATION_VIA_BUNDLER'
  )
  GROUP BY 1, 2, 3
),

-- Worldchain events
worldchain_events AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'worldchain_events_monthly' AS metric_name,
    SUM(count_events) AS amount
  FROM grouped_events
  WHERE event_type IN (
    'WORLDCHAIN_VERIFIED_USEROP',
    'WORLDCHAIN_NONVERIFIED_USEROP'
  )
  GROUP BY 1, 2, 3
),

-- Gas fees (including internal transactions)
gas_fees AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'gas_fees_monthly' AS metric_name,
    SUM(gas_fee) AS amount
  FROM grouped_events
  GROUP BY 1, 2, 3
),

-- Gas fees (outer transaction level only)
transaction_level_only_gas_fees AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'gas_fees_transaction_level_only_monthly' AS metric_name,
    SUM(gas_fee) AS amount
  FROM grouped_events
  WHERE event_type = 'CONTRACT_INVOCATION'
  GROUP BY 1, 2, 3
),

-- Defillama TVL
defillama_tvl_events AS (
  SELECT
    dl.project_id,
    UPPER(dl.from_artifact_namespace) AS chain,
    DATE_TRUNC('MONTH', dl.bucket_day::DATE) AS sample_date,
    dl.amount
  FROM oso.int_events_daily_to_project__defillama AS dl
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
    sample_date,
    'average_tvl_monthly' AS metric_name,
    SUM(amount) / DAY(DATE_ADD('MONTH', 1, sample_date) - INTERVAL '1' DAY)
      AS amount
  FROM defillama_tvl_events
  GROUP BY 1, 2, 3
),

-- Active Farcaster users
monthly_active_farcaster_users AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'active_farcaster_users_monthly' AS metric_name,
    APPROX_DISTINCT(from_artifact_id) AS amount
  FROM all_events
  WHERE is_farcaster_user = true
  GROUP BY 1, 2, 3
),

-- Active worldchain verified addresses
monthly_active_worldchain_verified_addresses AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'active_worldchain_verified_addresses_monthly' AS metric_name,
    APPROX_DISTINCT(from_artifact_id) AS amount
  FROM all_events
  WHERE event_type = 'WORLDCHAIN_VERIFIED_USEROP'
  GROUP BY 1, 2, 3
),

-- Active addresses
monthly_active_addresses AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'active_addresses_monthly' AS metric_name,
    APPROX_DISTINCT(from_artifact_id) AS amount
  FROM all_events
  GROUP BY 1, 2, 3
),

-- Qualified addresses
qualified_addresses AS (
  SELECT
    project_id,
    chain,
    sample_date,
    'qualified_addresses_monthly' AS metric_name,
    APPROX_DISTINCT(
      CASE
        WHEN event_type = 'WORLDCHAIN_VERIFIED_USEROP'
        OR is_farcaster_user = true
      THEN from_artifact_id
      ELSE NULL
      END
    ) AS amount
  FROM all_events
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
  FROM internal_transaction_count
  UNION ALL
  SELECT *
  FROM contract_invocations_count
  UNION ALL
  SELECT *
  FROM aa_userop_count
  UNION ALL
  SELECT *
  FROM worldchain_events
  UNION ALL
  SELECT *
  FROM gas_fees
  UNION ALL
  SELECT *
  FROM transaction_level_only_gas_fees
  UNION ALL
  SELECT *
  FROM defillama_tvl
  UNION ALL
  SELECT *
  FROM monthly_active_farcaster_users
  UNION ALL
  SELECT *
  FROM monthly_active_worldchain_verified_addresses
  UNION ALL
  SELECT *
  FROM monthly_active_addresses
  UNION ALL
  SELECT *
  FROM qualified_addresses
)

SELECT
  project_id::TEXT AS project_id,
  chain::TEXT AS chain,
  sample_date::TIMESTAMP AS sample_date,
  metric_name::TEXT AS metric_name,
  amount::DOUBLE AS amount
FROM union_all_metrics