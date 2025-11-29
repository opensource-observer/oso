MODEL (
  name oso.stg_unichain_logs__erc721,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
    on_destructive_change warn,
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    transaction_hash,
    log_index,
    contract_address
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "superchain",
    "incremental",
    "unichain",
  ),
);

SELECT
  @from_unix_timestamp(logs.block_timestamp) AS block_timestamp,
  logs.block_number,
  logs.block_hash,
  logs.transaction_hash,
  logs.transaction_index,
  logs.log_index,
  LOWER(logs.address) AS contract_address,
  logs.indexed_args.list AS indexed_args_list,
  logs.data,
  @chain_name(chain) AS chain
FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.logs') AS logs
WHERE
  logs.network = 'mainnet'
  AND logs.chain = 'unichain'
  AND logs.topic0 = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
  AND logs.dt BETWEEN @start_dt AND @end_dt