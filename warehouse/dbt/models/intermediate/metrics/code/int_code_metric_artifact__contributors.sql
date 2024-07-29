select
  events.to_artifact_id,
  events.event_source,
  time_intervals.time_interval,
  'contributor_count' as metric,
  COUNT(distinct events.from_artifact_id) as amount
from {{ ref('int_events_daily_to_artifact') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.event_type in (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'ISSUE_OPENED'
  )
  and events.bucket_day >= time_intervals.start_date
group by
  events.to_artifact_id,
  events.event_source,
  time_intervals.time_interval
