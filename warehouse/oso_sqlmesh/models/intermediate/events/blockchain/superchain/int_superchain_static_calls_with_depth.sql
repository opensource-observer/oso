MODEL (
  name oso.int_superchain_static_calls_with_depth,
  description 'Static calls with trace depth',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash, from_address, to_address, depth),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  )
);

SELECT
  block_timestamp,
  chain,
  transaction_hash,
  from_address,
  to_address,
  gas_used,
  trace_address,
  -- Trace depth is the number of elements in the trace_address string
  -- Example: trace_address = '16,2,2,6' -> Trace depth is 4
  cardinality(filter(split(regexp_replace(trace_address,'\\s',''),','),x->x<>'')) AS depth
FROM oso.stg_superchain__static_calls
WHERE block_timestamp BETWEEN @start_dt AND @end_dt