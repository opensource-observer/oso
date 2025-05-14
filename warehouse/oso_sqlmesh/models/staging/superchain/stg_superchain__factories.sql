MODEL (
  name oso.stg_superchain__factories,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 31
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain", "create_type"),
  grain (block_timestamp, chain_id, transaction_hash, deployer_address, contract_address),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := block_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
    ),
  )
);

@factory_deployments(
  @start_date,
  @end_date,
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces'),
  @chain_name(traces.chain) AS chain,
  transactions_time_partition_column := transactions.dt,
  traces_block_timestamp_column := @from_unix_timestamp(traces.block_timestamp),
  traces_time_partition_column := traces.dt
)