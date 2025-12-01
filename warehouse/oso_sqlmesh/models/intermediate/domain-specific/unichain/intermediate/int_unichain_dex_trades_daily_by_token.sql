MODEL (
  name oso.int_unichain_dex_trades_daily_by_token,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 90,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
    on_destructive_change warn,
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("bucket_day"),
  grain (bucket_day, dex_address, user_address, token_address),
  audits (has_at_least_n_rows(threshold := 0)),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "incremental",
    "superchain",
    "unichain",
  ),
);

WITH trades AS (
  SELECT
    DATE_TRUNC('DAY', block_timestamp) AS bucket_day,
    token0_address,
    token1_address,
    dex_address,
    user_address,
    transaction_hash
  FROM oso.int_unichain_dex_trades
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),

trades_by_token AS (
  SELECT
    bucket_day,
    token0_address AS token_address,
    dex_address,
    user_address,
    transaction_hash
  FROM trades
  UNION ALL
  SELECT
    bucket_day,
    token1_address AS token_address,
    dex_address,
    user_address,
    transaction_hash
  FROM trades
)

SELECT
  bucket_day,
  dex_address,
  user_address,
  token_address,
  COUNT(DISTINCT transaction_hash) AS trade_count
FROM trades_by_token
GROUP BY 1, 2, 3, 4
