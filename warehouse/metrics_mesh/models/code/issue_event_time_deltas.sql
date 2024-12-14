-- Model that records the delta (in seconds) since the creation of the issue or
-- pr.
MODEL (
  name metrics.issue_event_time_deltas,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (day("time"), "event_type"),
  grain (
    time,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id
  ),
);
select 
  `time`,
  event_type,
  event_source,
  @oso_id(
    event_source,
    to_artifact_id,
    issue_number
  ) as issue_id,
  issue_number,
  to_artifact_id,
  from_artifact_id,
  created_at,
  merged_at,
  closed_at,
  date_diff('second', created_at, `time`) as created_delta,
  case
    when merged_at is null then null
    else date_diff('second', merged_at, `time`)
  end as merged_delta,
  case
    when closed_at is null then null
    else date_diff('second', closed_at, `time`)
  end as closed_delta,
  comments
from @oso_source('timeseries_events_aux_issues_by_artifact_v0')