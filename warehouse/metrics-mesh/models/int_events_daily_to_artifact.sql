MODEL (
  name metrics.int_events_daily_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 90
  ),
  start '2015-01-01',
  cron '@daily',
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

with events as (
  select distinct
    from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    time,
    amount
  from @source("oso", "int_events")
  where time between @start_date and @end_date
)

select
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from events
group by
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  TIMESTAMP_TRUNC(time, day)
