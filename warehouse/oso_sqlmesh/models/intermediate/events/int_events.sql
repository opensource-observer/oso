MODEL (
  name oso.int_events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  time,
  to_artifact_id,
  from_artifact_id,
  UPPER(event_type) AS event_type,
  event_source_id::TEXT AS event_source_id,
  UPPER(event_source) AS event_source,
  LOWER(to_artifact_name) AS to_artifact_name,
  LOWER(to_artifact_namespace) AS to_artifact_namespace,
  UPPER(to_artifact_type) AS to_artifact_type,
  LOWER(to_artifact_source_id) AS to_artifact_source_id,
  LOWER(from_artifact_name) AS from_artifact_name,
  LOWER(from_artifact_namespace) AS from_artifact_namespace,
  UPPER(from_artifact_type) AS from_artifact_type,
  LOWER(from_artifact_source_id) AS from_artifact_source_id,
  amount::DOUBLE AS amount
FROM (
  SELECT
    *
  FROM oso.int_events__github
  WHERE
    time BETWEEN @start_dt AND @end_dt
  UNION ALL
  SELECT
    *
  FROM oso.int_events__dependencies
  WHERE
    time BETWEEN @start_dt AND @end_dt
  UNION ALL
  SELECT
    *
  FROM oso.int_events__funding
  WHERE
    time BETWEEN @start_dt AND @end_dt
)