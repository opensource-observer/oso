MODEL (
  name metrics.int_events_daily_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 30
  ),
  start '2015-01-01',
  cron '@daily',
  dialect 'clickhouse',
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  columns (
    bucket_day Date, 
    event_source String,
    event_type String,
    from_artifact_id String,
    to_artifact_id String,
    amount Int64
  )
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
  DATE_TRUNC(time, day) as bucket_day,
  SUM(amount) as amount
from events
group by
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC(time, day)
