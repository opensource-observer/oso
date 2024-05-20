select
  events.project_id,
  events.event_source,
  time_intervals.time_interval,
  'days_since_first_transaction' as metric,
  MAX(
    DATE_DIFF(
      CURRENT_DATE(),
      DATE(events.bucket_day),
      day
    )
  ) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
  and events.bucket_day >= time_intervals.start_date
group by
  events.project_id,
  events.event_source,
  time_intervals.time_interval
