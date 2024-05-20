select
  events.project_id,
  events.event_source as network,
  time_intervals.time_interval,
  'gas_fees' as metric,
  SUM(events.amount / 1e18) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  events.event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
  and events.bucket_day >= time_intervals.start_date
group by
  events.project_id,
  events.event_source,
  time_intervals.time_interval
