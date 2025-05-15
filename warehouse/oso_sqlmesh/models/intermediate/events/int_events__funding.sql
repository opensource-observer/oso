MODEL (
  name oso.int_events__funding,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 2,
    lookback 31
  ),
  start @funding_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
    "incrementalmusthaveforwardonly",
  )
);

WITH open_collective_expenses AS (
  SELECT
    time,
    event_type,
    event_source_id,
    event_source,
    to_artifact_id,
    to_name,
    to_namespace,
    to_type,
    to_artifact_source_id,
    from_artifact_id,
    from_name,
    from_namespace,
    from_type,
    from_artifact_source_id,
    amount
  FROM oso.stg_open_collective__expenses
  WHERE
    unit = 'USD' AND time BETWEEN @start_dt AND @end_dt
), open_collective_deposits AS (
  SELECT
    time,
    event_type,
    event_source_id,
    event_source,
    to_artifact_id,
    to_name,
    to_namespace,
    to_type,
    to_artifact_source_id,
    from_artifact_id,
    from_name,
    from_namespace,
    from_type,
    from_artifact_source_id,
    amount
  FROM oso.stg_open_collective__deposits
  WHERE
    unit = 'USD' AND time BETWEEN @start_dt AND @end_dt
), all_funding_events AS (
  SELECT
    *
  FROM open_collective_expenses
  UNION ALL
  SELECT
    *
  FROM open_collective_deposits
)
SELECT
  time,
  to_artifact_id,
  from_artifact_id,
  UPPER(event_type) AS event_type,
  event_source_id::VARCHAR AS event_source_id,
  UPPER(event_source) AS event_source,
  LOWER(to_name) AS to_artifact_name,
  LOWER(to_namespace) AS to_artifact_namespace,
  UPPER(to_type) AS to_artifact_type,
  LOWER(to_artifact_source_id) AS to_artifact_source_id,
  LOWER(from_name) AS from_artifact_name,
  LOWER(from_namespace) AS from_artifact_namespace,
  UPPER(from_type) AS from_artifact_type,
  LOWER(from_artifact_source_id) AS from_artifact_source_id,
  amount::DOUBLE AS amount
FROM all_funding_events