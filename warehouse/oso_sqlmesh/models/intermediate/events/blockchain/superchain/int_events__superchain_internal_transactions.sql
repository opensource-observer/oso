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
  partitioned_by (
    DAY("time"),
    "event_source",
    "event_type"
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95
    )
  ),
);

SELECT
  traces.block_timestamp AS time,
  'INTERNAL_TRANSACTION' AS event_type,
  traces.chain AS event_source,
  traces.transaction_hash,
  @oso_id(traces.chain, '', traces.transaction_hash) AS event_source_id,
  @oso_entity_id(traces.chain, '', transactions.from_address) AS from_artifact_id,
  '' AS from_artifact_namespace,
  transactions.from_address AS from_artifact_name,
  @oso_entity_id(traces.chain, '', traces.to_address) AS to_artifact_id,
  '' AS to_artifact_namespace,
  traces.to_address AS to_artifact_name,
  transactions.receipt_gas_used::DOUBLE * transactions.receipt_effective_gas_price::DOUBLE AS l2_gas_fee,
  COALESCE(traces.gas_used, 0)::DOUBLE AS gas_used_trace,
  CASE 
    WHEN gas_totals.total_gas_used = 0 OR gas_totals.total_gas_used IS NULL THEN 0.0
    ELSE (COALESCE(traces.gas_used, 0)::DOUBLE / gas_totals.total_gas_used::DOUBLE)
  END AS share_of_transaction_gas,
  (traces.to_address = transactions.to_address) AS is_top_level_transaction
FROM oso.stg_superchain__traces AS traces
JOIN oso.stg_superchain__transactions AS transactions
  ON transactions.transaction_hash = traces.transaction_hash
  AND transactions.chain = traces.chain
JOIN oso.int_superchain_traces_gas_used AS gas_totals
  ON gas_totals.transaction_hash = traces.transaction_hash
  AND gas_totals.chain = traces.chain
WHERE
  transactions.block_timestamp BETWEEN @start_dt AND @end_dt
  AND traces.block_timestamp BETWEEN @start_dt AND @end_dt
  AND transactions.receipt_status = 1