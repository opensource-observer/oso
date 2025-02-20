MODEL (
  name metrics.stg_superchain__potential_bots,
  kind FULL,
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("min_block_time")),
  grain (chain_name, address),
);

@potential_bots(
  @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions'),
  chain_name_column := transactions.chain,
  block_timestamp_column := @from_unix_timestamp(transactions.block_timestamp),
  time_partition_column := transactions.dt,
)