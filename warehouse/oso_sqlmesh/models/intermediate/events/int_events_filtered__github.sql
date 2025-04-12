MODEL (
  name oso.int_events_filtered__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT
  events.time,
  events.event_type,
  events.event_source,
  events.event_source_id,
  events.to_artifact_id,
  events.to_artifact_namespace,
  events.to_artifact_name,
  events.to_artifact_type,
  events.to_artifact_source_id,
  events.from_artifact_id,
  events.from_artifact_namespace,
  events.from_artifact_name,
  events.from_artifact_type,
  events.from_artifact_source_id,
  events.amount
FROM oso.int_events__github as events
WHERE
  events.time BETWEEN @start_dt AND @end_dt
  AND events.to_artifact_id IN (
    SELECT artifact_id FROM oso.int_repositories
  )
