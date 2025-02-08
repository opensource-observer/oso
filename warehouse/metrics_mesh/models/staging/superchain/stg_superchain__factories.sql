MODEL (
  name metrics.stg_superchain__factories,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 180,
    batch_concurrency 1,
    lookback 7
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain", "create_type"),
  grain (block_timestamp, chain_id, transaction_hash, deployer_address, contract_address)
);

@factory_deployments(
  @start_date,
  @end_date,
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces'),
  traces.chain as chain,
  transactions_time_partition_column := transactions.dt,
  traces_block_timestamp_column := @from_unix_timestamp(traces.block_timestamp),
  traces_time_partition_column := traces.dt,
)