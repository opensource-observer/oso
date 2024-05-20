select
  events.project_id,
  events.event_source,
  time_intervals.time_interval,
  'active_developer_count' as metric,
  COUNT(distinct events.from_artifact_id) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.event_type = 'COMMIT_CODE'
  and events.bucket_day >= time_intervals.start_date
group by
  events.project_id,
  events.event_source,
  time_intervals.time_interval
