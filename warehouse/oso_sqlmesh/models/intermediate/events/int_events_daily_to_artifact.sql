MODEL (
  name oso.int_events_daily_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  enabled false,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH events AS (
  SELECT DISTINCT
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    time,
    amount
  FROM oso.int_events
  WHERE
    time::DATE BETWEEN STRPTIME(@start_ds, '%Y-%m-%d')::DATE::DATE AND STRPTIME(@end_ds, '%Y-%m-%d')::DATE::DATE
)
SELECT
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  SUM(amount) AS amount
FROM events
GROUP BY
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE)