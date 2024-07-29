with user_stats as (
  select
    from_artifact_id,
    event_source,
    to_artifact_id,
    min(bucket_day) as first_day
  from {{ ref('int_events_daily_to_artifact') }}
  where
    event_type in (
      'COMMIT_CODE',
      'PULL_REQUEST_OPENED',
      'ISSUE_OPENED'
    )
  group by
    from_artifact_id,
    event_source,
    to_artifact_id
)

select
  events.to_artifact_id,
  events.event_source,
  time_intervals.time_interval,
  'new_contributor_count' as metric,
  count(
    distinct
    case
      when user_stats.first_day >= time_intervals.start_date
        then events.from_artifact_id
    end
  ) as amount
from {{ ref('int_events_daily_to_artifact') }} as events
inner join user_stats
  on
    events.from_artifact_id = user_stats.from_artifact_id
    and events.to_artifact_id = user_stats.to_artifact_id
    and events.event_source = user_stats.event_source
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
