MODEL (
  name oso.int_superchain_trace_level_events_by_project,
  description 'Events (down to trace level) involving known contracts with project-level attribution',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("block_timestamp"), "chain"),
  grain (
    block_timestamp,
    chain,
    transaction_hash,
    event_type,
    project_id,
    from_artifact_id
  )
);

/* Step 1: Get joined traces and transactions */
WITH base_transactions AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    from_address_tx,
    to_address_trace,
    to_address_tx,
    gas_used_tx * gas_price_tx / 1e18 AS gas_fee,
    @oso_id(chain, from_address_tx) AS from_address_tx_id,
    @oso_id(chain, to_address_trace) AS to_address_trace_id,
    @oso_id(chain, to_address_tx) AS to_address_tx_id
  FROM oso.int_superchain_traces_txs_joined
  WHERE
    block_timestamp BETWEEN @start_dt AND @end_dt
), addresses_by_project /* Step 2: Precompute address-to-project mapping */ AS (
  SELECT DISTINCT
    artifact_id,
    project_id
  FROM oso.int_artifacts_by_project
), transaction_level_events /* Step 3: Compute transaction and trace events */ AS (
  SELECT DISTINCT
    base_transactions.block_timestamp,
    base_transactions.chain,
    base_transactions.transaction_hash,
    base_transactions.from_address_tx_id AS from_artifact_id,
    base_transactions.gas_fee,
    abp.project_id,
    'TRANSACTION_EVENT' AS event_type
  FROM base_transactions
  INNER JOIN addresses_by_project AS abp
    ON base_transactions.to_address_tx_id = abp.artifact_id
), trace_level_events AS (
  SELECT DISTINCT
    base_transactions.block_timestamp,
    base_transactions.chain,
    base_transactions.transaction_hash,
    base_transactions.from_address_tx_id AS from_artifact_id,
    base_transactions.gas_fee,
    abp.project_id,
    'TRACE_EVENT' AS event_type
  FROM base_transactions
  INNER JOIN addresses_by_project AS abp
    ON base_transactions.to_address_trace_id = abp.artifact_id
)
/* Combine all events */
SELECT
  *
FROM transaction_level_events
UNION ALL
SELECT
  *
FROM trace_level_events