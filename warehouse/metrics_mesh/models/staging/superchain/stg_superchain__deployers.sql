MODEL (
  name metrics.stg_superchain__deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain_id"),
  grain (block_timestamp, chain_id, transaction_hash, deployer_address, contract_address)
);

@transactions_with_receipts_deployers(
  @start_dt,
  @end_dt,
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
  transactions.chain_id as chain_id,
  block_timestamp_column := @from_unix_timestamp(transactions.block_timestamp),
)