-- Blockchain events (currently only from the superchain dataset)
MODEL (
  name oso.int_events__blockchain,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 180,
    batch_concurrency 1,
    lookback 31,
    forward_only true,
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      missing_rate_min_threshold := 0.95,
    ),
  )
);


WITH txns AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    gas_price_tx,
    from_address_tx AS from_address,
    to_address_tx,
    to_address_trace,
    gas_used_tx,
    gas_used_trace
  FROM oso.int_superchain_traces_txs_joined
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),

internal_invocations AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    gas_price_tx,
    from_address,
    to_address_trace AS to_address,
    'CONTRACT_INTERNAL_INVOCATION' AS event_type,
    SUM(gas_used_trace) AS gas_used
  FROM txns
  WHERE to_address_trace != to_address_tx
  GROUP BY 1,2,3,4,5,6
),

contract_invocations AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    gas_price_tx,
    from_address,
    to_address_tx AS to_address,
    'CONTRACT_INVOCATION' AS event_type,
    gas_used_tx AS gas_used
  FROM txns
  WHERE to_address_trace = to_address_tx
),

events AS (
  SELECT * FROM internal_invocations
  UNION ALL
  SELECT * FROM contract_invocations
)

SELECT
  block_timestamp AS time,
  @oso_entity_id(chain, '', to_address) AS to_artifact_id,
  @oso_entity_id(chain, '', from_address) AS from_artifact_id,
  event_type,
  -- TODO: refactor to ensure unique event_source_id
  @oso_id(chain, '', transaction_hash) AS event_source_id,
  chain AS event_source,
  '' AS to_artifact_namespace,
  to_address AS to_artifact_name,
  to_address AS to_artifact_source_id,
  '' AS from_artifact_namespace,
  from_address AS from_artifact_name,
  from_address AS from_artifact_source_id,
  gas_used,
  gas_price_tx,
  transaction_hash
FROM events
