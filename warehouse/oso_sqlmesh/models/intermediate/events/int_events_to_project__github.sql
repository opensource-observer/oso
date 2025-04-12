MODEL (
  name oso.int_events_to_project__github,
  description 'All events to a project',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  artifacts.project_id,
  events.from_artifact_id,
  events.to_artifact_id,
  events.time,
  events.event_source,
  events.event_type,
  events.amount
FROM oso.int_events__github AS events
INNER JOIN oso.int_artifacts_by_project AS artifacts
  ON events.to_artifact_id = artifacts.artifact_id
WHERE
  events.time BETWEEN @start_dt AND @end_dt