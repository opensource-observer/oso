/* Model that records the delta (in seconds) since the creation of the issue or */ /* pr. */
MODEL (
  name oso.int_issue_event_time_deltas,
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
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
    ),
  )
);

SELECT
  "time",
  event_type,
  event_source,
  @oso_id(event_source, to_artifact_id, issue_number) AS issue_id,
  issue_number,
  to_artifact_id,
  from_artifact_id,
  created_at::TIMESTAMP,
  merged_at::TIMESTAMP,
  closed_at::TIMESTAMP,
  DATE_DIFF('SECOND', created_at, "time")::DOUBLE AS created_delta,
  CASE
    WHEN merged_at IS NULL
    THEN NULL
    ELSE DATE_DIFF('SECOND', merged_at, "time")
  END::DOUBLE AS merged_delta,
  CASE
    WHEN closed_at IS NULL
    THEN NULL
    ELSE DATE_DIFF('SECOND', closed_at, "time")
  END::DOUBLE AS closed_delta,
  comments::DOUBLE
FROM oso.int_events_aux_issues
WHERE
  "time" BETWEEN @start_dt AND @end_dt