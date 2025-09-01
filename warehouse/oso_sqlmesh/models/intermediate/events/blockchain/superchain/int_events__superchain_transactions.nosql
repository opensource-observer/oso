MODEL (
  name oso.int_events__superchain_transactions,
  description 'Transaction level events for Superchain',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
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
      missing_rate_min_threshold := 0.95,
    ),
  ),
  enabled false,
);

SELECT
  block_timestamp AS time,
  CASE
    WHEN receipt_status = 1 THEN 'TRANSACTION'
    ELSE 'FAILED_TRANSACTION'
  END AS event_type,
  chain AS event_source,
  @oso_id(chain, '', transaction_hash) AS event_source_id,
  @oso_entity_id(chain, '', from_address) AS from_artifact_id,
  '' AS from_artifact_namespace,
  from_address AS from_artifact_name,
  @oso_entity_id(chain, '', to_address) AS to_artifact_id,
  '' AS to_artifact_namespace,
  to_address AS to_artifact_name,
  transaction_type,
  CAST(receipt_effective_gas_price * receipt_gas_used AS DOUBLE) AS l2_gas_fee,
  CAST(receipt_l1_fee AS DOUBLE) AS l1_gas_fee,
  transaction_hash
FROM oso.stg_superchain__transactions
WHERE
  block_timestamp BETWEEN @start_dt AND @end_dt
