MODEL (
  name oso.int_superchain_events_by_project,
  kind incremental_by_time_range(
   time_column time,
   batch_size 60,
   batch_concurrency 2,
   lookback 31
  ),
  start '2024-09-01',
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain (time, event_type, event_source, event_type, from_artifact_id, to_artifact_id, transaction_hash),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
    "incrementalmusthaveforwardonly",
  )
);

WITH unioned_events AS (
  SELECT
    time,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id,
    transaction_hash,
    (userop_gas_cost::DOUBLE / 1e18)::DOUBLE AS gas_fee
  FROM oso.int_events__4337
  WHERE time BETWEEN @start_dt AND @end_dt
  UNION ALL
  SELECT
    time,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id,
    transaction_hash,
    (gas_used::DOUBLE * gas_price_tx::DOUBLE / 1e18)::DOUBLE AS gas_fee
  FROM oso.int_events__blockchain
  WHERE time BETWEEN @start_dt AND @end_dt
)

SELECT
  e.time,
  e.event_type,
  e.event_source,
  e.from_artifact_id,
  e.to_artifact_id,
  e.gas_fee,
  e.transaction_hash,
  abp.project_id as project_id
FROM unioned_events AS e
INNER JOIN oso.artifacts_by_project_v1 AS abp
  ON e.to_artifact_id = abp.artifact_id
INNER JOIN oso.int_superchain_chain_names AS chain_names
  ON e.event_source = chain_names.chain
