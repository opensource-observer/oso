MODEL (
  name oso.stg_optimism__enriched_logs,
  kind INCREMENTAL_BY_TIME_RANGE(
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
    on_destructive_change warn
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("block_timestamp"),
  grain(
    block_timestamp,
    transaction_hash,
    log_index
  ),
  audits(
    has_at_least_n_rows(threshold := 0)
  ),
  ignored_rules(
    "incrementalmustdefinenogapsaudit"
  ),
  tags(
    "superchain",
    "incremental",
    "optimism"
  )
);

WITH logs AS (
  SELECT
    dt,
    block_timestamp,
    transaction_hash,
    log_index,
    topic0,
    data AS data_hex,
    indexed_args.list AS indexed_args_list,
    address AS contract_address
  FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.logs')
  WHERE
    network = 'mainnet'
    AND chain = 'op'
    AND dt BETWEEN @start_dt AND @end_dt
    AND address = '0x4200000000000000000000000000000000000042'
),

txs AS (
  SELECT
    dt,
    block_timestamp,
    hash AS transaction_hash,
    input AS input_hex,
    value_lossless,
    from_address,
    to_address
  FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.transactions')
  WHERE
    network = 'mainnet'
    AND chain = 'op'
    AND receipt_status = 1
    AND dt BETWEEN @start_dt AND @end_dt
),

enriched_logs AS (
  SELECT
    l.dt,
    @from_unix_timestamp(l.block_timestamp) AS block_timestamp,
    l.transaction_hash,
    l.log_index,
    l.contract_address,
    t.from_address,
    t.to_address,
    value_lossless,
    substr(t.input_hex,1,10) AS function_selector,
    l.topic0,
    l.data_hex,
    l.indexed_args_list
  FROM logs AS l
  JOIN txs AS t
    ON l.transaction_hash = t.transaction_hash
   AND l.dt = t.dt
)

SELECT
  block_timestamp,
  transaction_hash,
  log_index,
  contract_address,
  from_address,
  to_address,
  topic0,
  function_selector,
  data_hex,
  value_lossless,
  indexed_args_list
FROM enriched_logs