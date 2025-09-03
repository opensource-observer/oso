MODEL (
  name oso.int_events__superchain_internal_transactions,
  description 'Internal transaction (trace-level) events for Superchain',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true
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
  block_timestamp AS time,
  'INTERNAL_TRANSACTION' AS event_type,
  chain AS event_source,
  transaction_hash,
  @oso_id(chain, '', transaction_hash) AS event_source_id,
  @oso_entity_id(chain, '', from_address_tx) AS from_artifact_id,
  '' AS from_artifact_namespace,
  from_address_tx AS from_artifact_name,
  @oso_entity_id(chain, '', to_address_trace) AS to_artifact_id,
  '' AS to_artifact_namespace,
  to_address_trace AS to_artifact_name,
  gas_used_tx::DOUBLE * gas_price_tx::DOUBLE AS l2_gas_fee,
  COALESCE(gas_used_trace, 0)::DOUBLE AS gas_used_trace,
  COALESCE(gas_used_trace, 0)::DOUBLE / NULLIF(
    SUM(COALESCE(gas_used_trace, 0)::DOUBLE) OVER (
      PARTITION BY chain, transaction_hash
    ), 0
  ) AS share_of_transaction_gas,
  (to_address_trace=to_address_tx) AS is_top_level_transaction
FROM oso.int_superchain_traces_txs_joined
WHERE block_timestamp BETWEEN @start_dt AND @end_dt