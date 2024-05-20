with user_stats as (
  select
    events.from_artifact_id,
    events.event_source,
    time_intervals.time_interval,
    COUNT(distinct events.project_id) as project_count
  from {{ ref('int_events_daily_to_project') }} as events
  cross join {{ ref('int_time_intervals') }} as time_intervals
  where
    events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and events.bucket_day >= time_intervals.start_date
  group by
    events.from_artifact_id,
    events.event_source,
    time_intervals.time_interval
)

select
  events.project_id,
  events.event_source,
  time_intervals.time_interval,
  'multi_project_address_count' as metric,
  COUNT(distinct events.from_artifact_id) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
left join user_stats
  on
    events.from_artifact_id = user_stats.from_artifact_id
    and events.event_source = user_stats.event_source
    and time_intervals.time_interval = user_stats.time_interval
where
  events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  and events.bucket_day >= time_intervals.start_date
  and user_stats.project_count > 2
group by
  events.project_id,
  events.event_source,
  time_intervals.time_interval
