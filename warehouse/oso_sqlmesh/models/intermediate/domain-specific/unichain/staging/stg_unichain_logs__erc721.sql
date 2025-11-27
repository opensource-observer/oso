MODEL (
  name oso.stg_unichain_logs__erc721,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    log_index,
    contract_address,
    token_id
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

WITH raw_logs AS (
  SELECT
    logs.block_timestamp,
    logs.block_number,
    logs.block_hash,
    logs.transaction_hash,
    logs.transaction_index,
    logs.log_index,
    logs.address AS contract_address,
    logs.topic0,
    logs.indexed_args.list AS indexed_args_list,
    logs.data,
    logs.chain
  FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.logs') AS logs
  WHERE
    logs.network = 'mainnet'
    AND logs.chain = 'unichain'
    AND logs.topic0 = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    AND /* Bigquery requires we specify partitions to filter for this data source */ logs.dt BETWEEN @start_dt AND @end_dt
),

parsed_logs AS (
  SELECT
    raw_logs.block_timestamp,
    raw_logs.block_number,
    raw_logs.block_hash,
    raw_logs.transaction_hash,
    raw_logs.transaction_index,
    raw_logs.log_index,
    raw_logs.contract_address,
    raw_logs.chain,
    -- Extract from_address from indexed_args.list[1] (topic1, first indexed parameter)
    LOWER(
      CONCAT(
        '0x',
        SUBSTRING(indexed_args_list[1].element, 27)
      )
    ) AS from_address,
    -- Extract to_address from indexed_args.list[2] (topic2, second indexed parameter)
    LOWER(
      CONCAT(
        '0x',
        SUBSTRING(indexed_args_list[2].element, 27)
      )
    ) AS to_address,
    -- Extract token_id from data field (uint256, 64 hex characters)
    @safe_hex_to_int(SUBSTRING(raw_logs.data, 3, 64)) AS token_id
  FROM raw_logs
)

SELECT
  @from_unix_timestamp(block_timestamp) AS block_timestamp,
  block_number,
  block_hash,
  transaction_hash,
  transaction_index,
  log_index,
  LOWER(contract_address) AS contract_address,
  from_address,
  to_address,
  token_id,
  @chain_name(chain) AS chain
FROM parsed_logs

