-- 4337 events (currently only from the superchain dataset)
MODEL (
  name oso.int_events__4337,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 180,
    batch_concurrency 1,
    lookback 31
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
    ),
  )
);

WITH filtered_events AS (
  SELECT
    chain,
    block_timestamp,
    transaction_hash,
    userop_hash,
    from_address,
    to_address,
    bundler_address,
    paymaster_address,
    userop_gas_cost,
    userop_gas_used
  FROM oso.stg_superchain__4337_traces
  WHERE block_timestamp BETWEEN @start_dt AND @end_dt
),

to_events AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    userop_hash,
    from_address,
    to_address,
    userop_gas_cost,
    userop_gas_used,
    'CONTRACT_INVOCATION_VIA_USEROP' AS event_type
  FROM filtered_events
),

paymaster_events AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    userop_hash,
    from_address,
    paymaster_address AS to_address,
    userop_gas_cost,
    userop_gas_used,
    'CONTRACT_INVOCATION_VIA_PAYMASTER' AS event_type
  FROM filtered_events
),

bundler_events AS (
  SELECT
    block_timestamp,
    chain,
    transaction_hash,
    userop_hash,
    from_address,
    bundler_address AS to_address,
    userop_gas_cost,
    userop_gas_used,
    'CONTRACT_INVOCATION_VIA_BUNDLER' AS event_type
  FROM filtered_events
),

unioned_events AS (
  SELECT
    *
  FROM to_events
  UNION ALL
  SELECT
    *
  FROM paymaster_events
  UNION ALL
  SELECT
    *
  FROM bundler_events
)

SELECT
  block_timestamp AS time,
  @oso_entity_id(chain, '', to_address) AS to_artifact_id,
  @oso_entity_id(chain, '', from_address) AS from_artifact_id,
  event_type,
  @oso_id(chain, '', transaction_hash) AS event_source_id,
  chain AS event_source,
  '' AS to_artifact_namespace,
  to_address AS to_artifact_name,
  to_address AS to_artifact_source_id,
  '' AS from_artifact_namespace,
  from_address AS from_artifact_name,
  from_address AS from_artifact_source_id,
  userop_gas_used::DOUBLE AS userop_gas_used,
  userop_gas_cost::DOUBLE AS userop_gas_cost,
  transaction_hash,
  userop_hash
FROM unioned_events