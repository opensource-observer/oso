MODEL (
  name oso.stg_superchain__4337_userop_logs,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 180,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    userop_hash,
    sender_address,
    paymaster_address,
    contract_address
  ),
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
  transaction_hash,
  log_index,
  userophash AS userop_hash,
  sender AS sender_address,
  paymaster AS paymaster_address,
  contract_address,
  actualgascost::DOUBLE AS userop_gas_price,
  actualgasused::DOUBLE AS userop_gas_used,
  @chain_name(chain) AS chain
FROM @oso_source(
  'bigquery.optimism_superchain_4337_account_abstraction_data.useroperationevent_logs_v2'
)
WHERE
  network = 'mainnet'
  AND success = TRUE
  AND /* Bigquery requires we specify partitions to filter for this data source */ dt BETWEEN @start_dt AND @end_dt