MODEL (
  name metrics.timeseries_events_by_artifact_v0,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  partitioned_by (DAY("time"), "event_type")
);

select
  time,
  to_artifact_id,
  from_artifact_id,
  event_type,
  event_source_id,
  event_source,
  amount
from metrics.int_events
where time between @start_dt and @end_dt