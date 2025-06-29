MODEL (
  name oso.stg_superchain__7702_transactions,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start '2025-05-07',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (block_timestamp, chain, transaction_hash, from_address, to_address),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "superchain",
    "incremental",
  ),

);

SELECT
  @from_unix_timestamp(block_timestamp) AS block_timestamp,
  "hash" AS transaction_hash,
  from_address,
  to_address,
  @chain_name(chain) AS chain
FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions')
WHERE
  network = 'mainnet'
  AND receipt_status = 1
  AND transaction_type = 4
  AND /* Bigquery requires we specify partitions to filter for this data source */ dt BETWEEN @start_dt AND @end_dt