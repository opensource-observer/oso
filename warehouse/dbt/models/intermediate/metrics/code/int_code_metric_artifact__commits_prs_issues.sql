select
  events.to_artifact_id,
  events.event_source,
  time_intervals.time_interval,
  CONCAT(LOWER(events.event_type), '_count') as metric,
  SUM(events.amount) as amount
from {{ ref('int_events_daily_to_artifact') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.bucket_day >= time_intervals.start_date
  and events.event_type in (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_MERGED',
    'ISSUE_OPENED',
    'ISSUE_CLOSED'
  )
group by
  events.to_artifact_id,
  events.event_source,
  time_intervals.time_interval,
  events.event_type
