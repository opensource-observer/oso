MODEL (
  name oso.stg_superchain__proxies,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain_id,
    id,
    transaction_hash,
    from_address,
    to_address,
    proxy_type,
    proxy_address
  ),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      audit_date_part := 'day',
    ),
  )
);

@known_proxies(
  @start_dt,
  @end_dt,
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces'),
  @chain_name(traces.chain) AS chain,
  block_timestamp_column := @from_unix_timestamp(traces.block_timestamp),
  time_partition_column := traces.dt
)