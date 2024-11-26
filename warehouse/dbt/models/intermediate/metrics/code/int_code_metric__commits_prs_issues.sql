select
  events.project_id,
  events.event_source,
  time_intervals.time_interval,
  CONCAT(LOWER(events.event_type), '_count') as metric,
  SUM(events.amount) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.bucket_day >= time_intervals.start_date
  and events.event_type in (
    'COMMIT_CODE',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_MERGED',
    'PULL_REQUEST_REVIEW_COMMENT',
    'ISSUE_OPENED',
    'ISSUE_CLOSED',
    'ISSUE_COMMENT',
    'RELEASE_PUBLISHED'
  )
group by
  events.project_id,
  events.event_source,
  time_intervals.time_interval,
  events.event_type
