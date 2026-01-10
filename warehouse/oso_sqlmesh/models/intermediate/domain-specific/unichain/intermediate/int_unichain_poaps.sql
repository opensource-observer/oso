MODEL (
  name oso.int_unichain_poaps,
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
  partitioned_by DAY("block_timestamp"),
  grain (block_timestamp, transaction_hash, from_address, to_address, token_id),
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
    block_timestamp,
    transaction_hash,
    contract_address,
    indexed_args_list
  FROM oso.stg_unichain_logs__transfers
  WHERE
    block_timestamp BETWEEN @start_dt AND @end_dt
    AND contract_address = '0x22c1f6050e56d2876009903609a2cc3fef83b415'
    AND CARDINALITY(indexed_args_list) >= 3
),

parsed_logs AS (
  SELECT
    block_timestamp,
    transaction_hash,
    contract_address,
    -- from_address from topic1
    LOWER(
      CONCAT(
        '0x',
        SUBSTRING(indexed_args_list[1].element,27)
      )
    ) AS from_address,

    -- to_address from topic2
    LOWER(
      CONCAT(
        '0x',
        SUBSTRING(indexed_args_list[2].element,27)
      )
    ) AS to_address,

    -- token_id from topic3
    @safe_hex_to_int(SUBSTRING(indexed_args_list[3].element,3)) AS token_id
  FROM raw_logs
)

SELECT
  block_timestamp,
  transaction_hash,
  contract_address,
  from_address,
  to_address,
  token_id
FROM parsed_logs