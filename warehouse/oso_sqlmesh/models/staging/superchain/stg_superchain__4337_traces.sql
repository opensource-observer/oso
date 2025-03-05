MODEL (
  name oso.stg_superchain__4337_traces,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 180,
    batch_concurrency 1,
    lookback 7
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    userop_hash,
    from_address,
    to_address,
    sender_address,
    paymaster_address,
    method_id
  )
);

SELECT
  @from_unix_timestamp(block_timestamp) AS block_timestamp,
  transaction_hash,
  userop_hash,
  from_address,
  to_address,
  userop_sender AS sender_address,
  userop_paymaster AS paymaster_address,
  useropevent_actualgascost::BIGINT AS userop_gas_price,
  useropevent_actualgasused::BIGINT AS userop_gas_used,
  value::BIGINT AS value,
  method_id,
  @chain_name(chain) AS chain
FROM @oso_source(
  'bigquery.optimism_superchain_4337_account_abstraction_data.enriched_entrypoint_traces_v1'
)
WHERE
  network = 'mainnet'
  AND status = 1
  AND trace_type IN ('call', 'create', 'create2')
  AND call_type <> 'staticcall'
  AND useropevent_success = TRUE
  AND /* Bigquery requires we specify partitions to filter for this data source */ dt BETWEEN @start_dt AND @end_dt