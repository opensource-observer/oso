MODEL (
  name oso.int_events__worldchain_userops,
  description 'Worldchain user events',
  kind incremental_by_time_range(
   time_column time,
   batch_size 60,
   batch_concurrency 3,
   lookback 31
  ),
  start '2024-09-01',
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
    "incrementalmustdefinenogapsaudit",
  )
);

WITH base_events AS (
  SELECT
    traces.block_timestamp AS time,
    traces.chain AS event_source,
    traces.from_address_trace AS from_artifact_name,
    traces.to_address_trace AS to_artifact_name,
    CASE 
      WHEN
        users.verified_address IS NOT NULL
        AND users.verified_until > traces.block_timestamp 
      THEN 'WORLDCHAIN_VERIFIED_USEROP'
      ELSE 'WORLDCHAIN_NONVERIFIED_USEROP'
    END AS event_type,
    traces.transaction_hash,
    traces.gas_used_trace * traces.gas_price_tx / 1e18 AS userop_gas_cost
  FROM oso.int_superchain_traces_txs_joined AS traces
  LEFT JOIN oso.int_worldchain_verified_addresses AS users
    ON traces.from_address_trace = users.verified_address
  WHERE
    traces.block_timestamp BETWEEN @start_dt AND @end_dt
    AND traces.chain = 'WORLDCHAIN'
)

SELECT
  time,
  event_type,
  event_source,
  from_artifact_name,
  to_artifact_name,
  @oso_entity_id(event_source, '', from_artifact_name) AS from_artifact_id,
  @oso_entity_id(event_source, '', from_artifact_name) AS to_artifact_id,
  transaction_hash,
  userop_gas_cost
FROM base_events
