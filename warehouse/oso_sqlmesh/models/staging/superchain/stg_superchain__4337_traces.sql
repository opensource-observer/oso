MODEL (
  name oso.stg_superchain__4337_traces,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 31
  ),
  dialect trino,
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    userop_hash,
    from_address,
    to_address,
    bundler_address,
    userop_paymaster,
    method_id
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  )
);

SELECT
  @chain_name(chain) AS chain,
  @from_unix_timestamp(block_timestamp) AS block_timestamp,
  transaction_hash,
  userop_hash,
  method_id,
  from_address,
  to_address,
  bundler_address AS bundler_address,
  userop_paymaster AS paymaster_address,
  useropevent_actualgascost::DOUBLE AS userop_gas_cost,
  useropevent_actualgasused::DOUBLE AS userop_gas_used,
  CAST(
    CASE WHEN input != '0x' 
      THEN 0 
      ELSE TRY(@hex_to_int(SUBSTRING(userop_calldata, 75, 64))) / CAST(1e18 AS DECIMAL(38,18))
    END AS DECIMAL(38,18)
  ) AS value
FROM @oso_source(
  'bigquery.optimism_superchain_4337_account_abstraction_data.enriched_entrypoint_traces_v2'
)
WHERE
  network = 'mainnet'
  AND status = 1
  AND trace_type IN ('call', 'create', 'create2')
  AND call_type <> 'staticcall'
  AND useropevent_success = TRUE
  AND is_from_sender = TRUE
  AND userop_idx = 1
  AND /* Bigquery requires we specify partitions to filter for this data source */ dt BETWEEN @start_dt AND @end_dt