{% set fulltime_dev_days = 10 %}

with dev_stats as (
  select
    events.project_id,
    events.event_source,
    time_intervals.time_interval,
    events.from_artifact_id,
    TIMESTAMP_TRUNC(events.bucket_day, month) as bucket_month,
    COUNT(distinct events.bucket_day) as amount
  from {{ ref('int_events_daily_to_project') }} as events
  cross join {{ ref('int_time_intervals') }} as time_intervals
  where
    events.event_type = 'COMMIT_CODE'
    and events.bucket_day >= time_intervals.start_date
  group by
    events.project_id,
    events.event_source,
    time_intervals.time_interval,
    events.from_artifact_id,
    TIMESTAMP_TRUNC(events.bucket_day, month)
)

select
  project_id,
  event_source,
  time_interval,
  'fulltime_developer_average' as metric,
  (
    COUNT(distinct from_artifact_id)
    / COUNT(distinct bucket_month)
  ) as amount
from dev_stats
where amount >= {{ fulltime_dev_days }}
group by
  project_id,
  event_source,
  time_interval
