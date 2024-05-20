select
  events.project_id,
  events.event_source as network,
  time_intervals.time_interval,
  'transaction_count' as metric,
  SUM(events.amount) as amount
from {{ ref('int_events_daily_to_project') }} as events
cross join {{ ref('int_time_intervals') }} as time_intervals
inner join {{ ref('int_artifacts_by_user') }} as artifacts_by_user
  on events.from_artifact_id = artifacts_by_user.artifact_id
where
  events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  and events.bucket_day >= time_intervals.start_date
  and artifacts_by_user.user_id is not null
group by
  events.project_id,
  events.event_source,
  time_intervals.time_interval
