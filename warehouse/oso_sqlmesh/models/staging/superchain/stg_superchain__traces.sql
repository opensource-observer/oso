MODEL (
  name oso.stg_superchain__traces,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash, from_address, to_address)
);

SELECT
  @from_unix_timestamp(block_timestamp) AS block_timestamp,
  transaction_hash,
  from_address,
  to_address,
  gas_used,
  @chain_name(chain) AS chain
FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces')
WHERE
  network = 'mainnet'
  AND "status" = 1
  AND call_type IN ('delegatecall', 'call')
  AND gas_used > 0
  AND /* Bigquery requires we specify partitions to filter for this data source */ dt BETWEEN @start_dt AND @end_dt