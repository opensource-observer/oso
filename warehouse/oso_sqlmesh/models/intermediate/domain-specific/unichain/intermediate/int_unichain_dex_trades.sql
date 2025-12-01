MODEL (
  name oso.int_unichain_dex_trades,
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
  grain (block_timestamp, transaction_hash),
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
    log_index,
    contract_address,
    indexed_args_list,
    data AS data_hex
  FROM oso.stg_unichain_logs__transfers
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
    AND CARDINALITY(indexed_args_list) >= 2
),

parsed_transfers AS (
  SELECT
    block_timestamp,
    transaction_hash,
    log_index,
    LOWER(contract_address) AS token_address,
    amount_hex,
    @safe_hex_to_int(amount_hex) AS amount,
    CASE
      WHEN indexed_args_list[1].element IS NOT NULL THEN LOWER(
        CONCAT('0x', SUBSTRING(indexed_args_list[1].element, 27))
      )
    END AS from_address,
    CASE
      WHEN indexed_args_list[2].element IS NOT NULL THEN LOWER(
        CONCAT('0x', SUBSTRING(indexed_args_list[2].element, 27))
      )
    END AS to_address,
    ROW_NUMBER() OVER (PARTITION BY transaction_hash ORDER BY log_index) AS transfer_index
  FROM (
    SELECT
      block_timestamp,
      transaction_hash,
      log_index,
      contract_address,
      indexed_args_list,
      CASE 
        WHEN data_hex IS NOT NULL AND data_hex != '0x' AND LENGTH(data_hex) >= 3 THEN
          SUBSTRING(
            CASE WHEN data_hex LIKE '0x%' THEN SUBSTRING(data_hex, 3) ELSE data_hex END,
            GREATEST(
              1,
              LENGTH(CASE WHEN data_hex LIKE '0x%' THEN SUBSTRING(data_hex, 3) ELSE data_hex END) - 63
            )
          )
        ELSE NULL
      END AS amount_hex
    FROM raw_logs
  ) t
),

swaps AS (
  SELECT
    t1.block_timestamp,
    t1.transaction_hash,
    t1.token_address AS token0_address,
    t2.token_address AS token1_address,
    t1.amount AS amount0,
    t2.amount AS amount1,
    t1.amount_hex AS hex_amount0,
    t2.amount_hex AS hex_amount1,
    t1.from_address AS token0_from_address,
    t1.to_address AS token0_to_address,
    t2.from_address AS token1_from_address,
    t2.to_address AS token1_to_address,
    CASE
      WHEN t1.from_address = t2.to_address THEN t1.from_address
      WHEN t1.to_address = t2.from_address THEN t1.to_address
      WHEN t1.from_address = t2.from_address THEN t1.from_address
      WHEN t1.to_address = t2.to_address THEN t1.to_address
      ELSE NULL
    END AS user_address,
    CASE
      WHEN t1.from_address = t2.to_address THEN t1.to_address
      WHEN t1.to_address = t2.from_address THEN t1.from_address
      WHEN t1.from_address = t2.from_address AND t1.to_address != t2.to_address THEN t1.to_address
      WHEN t1.to_address = t2.to_address AND t1.from_address != t2.from_address THEN t1.from_address
      ELSE NULL
    END AS dex_address
  FROM parsed_transfers t1
  JOIN parsed_transfers t2
    ON t1.transaction_hash = t2.transaction_hash
    AND t2.transfer_index = t1.transfer_index + 1
  WHERE
    t1.transfer_index % 2 = 1
    AND (
      t1.to_address = t2.from_address
      OR t1.from_address = t2.to_address
      OR t1.to_address = t2.to_address
      OR t1.from_address = t2.from_address
    )
)
    
SELECT
  block_timestamp,
  transaction_hash,
  token0_address,
  token1_address,
  amount0,
  amount1,
  hex_amount0,
  hex_amount1,
  user_address,
  dex_address
FROM swaps