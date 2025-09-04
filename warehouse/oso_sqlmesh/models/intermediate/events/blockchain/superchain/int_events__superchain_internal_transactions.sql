MODEL (
  name oso.int_events__superchain_internal_transactions,
  description 'Internal transaction (trace-level) events for Superchain',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
    on_destructive_change warn
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_source", "event_type"),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95
    )
  )
);

WITH traces_f AS (
  SELECT
    chain,
    block_timestamp,
    transaction_hash,
    to_address,
    CAST(COALESCE(gas_used, 0) AS DOUBLE) AS gas_used_d
  FROM oso.stg_superchain__traces
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),
tx_f AS (
  SELECT
    chain,
    block_timestamp,
    transaction_hash,
    from_address,
    to_address,
    CAST(receipt_gas_used AS DOUBLE) AS receipt_gas_used_d,
    CAST(receipt_effective_gas_price AS DOUBLE) AS receipt_eff_gas_price_d
  FROM oso.stg_superchain__transactions
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
    AND receipt_status = 1
),
gas_totals AS (
  SELECT
    chain,
    transaction_hash,
    SUM(gas_used_d) AS total_gas_used_d
  FROM traces_f
  GROUP BY 1, 2
)

SELECT
  t.block_timestamp AS time,
  'INTERNAL_TRANSACTION' AS event_type,
  t.chain AS event_source,
  t.transaction_hash,
  @oso_id(t.chain, '', t.transaction_hash) AS event_source_id,
  @oso_entity_id(t.chain, '', x.from_address) AS from_artifact_id,
  '' AS from_artifact_namespace,
  x.from_address AS from_artifact_name,
  @oso_entity_id(t.chain, '', t.to_address) AS to_artifact_id,
  '' AS to_artifact_namespace,
  t.to_address AS to_artifact_name,
  x.receipt_gas_used_d * x.receipt_eff_gas_price_d AS l2_gas_fee,
  t.gas_used_d AS gas_used_trace,
  CASE 
    WHEN g.total_gas_used_d IS NULL OR g.total_gas_used_d = 0 THEN 0.0
    ELSE t.gas_used_d / g.total_gas_used_d
  END AS share_of_transaction_gas,
  (t.to_address = x.to_address) AS is_top_level_transaction
FROM traces_f AS t
JOIN gas_totals AS g
  ON g.chain = t.chain 
  AND g.transaction_hash = t.transaction_hash
JOIN tx_f AS x
  ON x.chain = t.chain 
  AND x.transaction_hash = t.transaction_hash
  