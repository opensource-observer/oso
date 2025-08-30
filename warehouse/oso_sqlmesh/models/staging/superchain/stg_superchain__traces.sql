MODEL (
  name oso.stg_superchain__traces,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash, from_address, to_address),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      ignore_after := @superchain_audit_end,
      missing_rate_min_threshold := 0.95,
    ),
  ),
  tags (
    "superchain",
    "incremental",
  ),
);

SELECT
  @from_unix_timestamp(block_timestamp) AS block_timestamp,
  block_number,
  block_hash,
  transaction_index,
  transaction_hash,
  from_address,
  to_address,
  gas,
  gas_used,
  subtraces,
  trace_address,
  @chain_name(chain) AS chain,
  call_type
FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces')
WHERE
  network = 'mainnet'
  AND "status" = 1
  AND call_type IN ('delegatecall', 'call')
  AND gas_used > 0
  AND /* Bigquery requires we specify partitions to filter for this data source */ dt BETWEEN @start_dt AND @end_dt