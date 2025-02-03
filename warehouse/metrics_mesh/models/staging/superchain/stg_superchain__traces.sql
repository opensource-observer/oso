MODEL (
  name metrics.stg_superchain__traces,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash, from_address, to_address)
);

select
  @from_unix_timestamp(block_timestamp) as block_timestamp,
  transaction_hash,
  from_address,
  to_address,
  gas_used,
  upper(
    case
      when chain = 'op' then 'optimism'
      when chain = 'fraxtal' then 'frax'
      else chain
    end
  ) as chain
from @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces')
where
  network = 'mainnet'
  and "status" = 1
  and call_type in ('delegatecall', 'call')
  and gas_used > 0
  -- Bigquery requires we specify partitions to filter for this data source
  and dt between @start_dt and @end_dt
