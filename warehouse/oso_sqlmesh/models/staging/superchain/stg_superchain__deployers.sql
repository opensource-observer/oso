MODEL (
  name oso.stg_superchain__deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain_id, transaction_hash, deployer_address, contract_address),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      missing_rate_min_threshold := 0.95,
    ),
  ),
  tags (
    "superchain",
    "incremental",
  ),
);

@transactions_with_receipts_deployers(
  @start_dt,
  @end_dt,
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
  @chain_name(transactions.chain) AS chain,
  block_timestamp_column := @from_unix_timestamp(transactions.block_timestamp),
  time_partition_column := transactions.dt
)