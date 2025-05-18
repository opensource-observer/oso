MODEL (
  name oso.int_events_to_collection,
  description 'All events to a collection',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 2,
    lookback 31
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  enabled false,
  tags (
    'entity_category=collection',
    "incremental"
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
    ),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
  )
);

SELECT
  collections.collection_id,
  int_events_to_project.project_id,
  int_events_to_project.from_artifact_id,
  int_events_to_project.to_artifact_id,
  int_events_to_project.time,
  int_events_to_project.event_source,
  int_events_to_project.event_type,
  int_events_to_project.amount
FROM oso.int_events_to_project__github
INNER JOIN oso.int_projects_by_collection AS collections
  ON int_events_to_project.project_id = collections.project_id
WHERE
  int_events_to_project.time BETWEEN @start_dt AND @end_dt
