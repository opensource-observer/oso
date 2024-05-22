with user_stats as (
  select
    trusted_user_id,
    MIN(bucket_day) as first_day
  from {{ ref('rf4_events_daily_to_project') }}
  where trusted_user_id is not null
  group by trusted_user_id
),

first_txns as (
  select
    events.project_id,
    events.trusted_user_id,
    events.bucket_day,
    user_stats.first_day
  from {{ ref('rf4_events_daily_to_project') }} as events
  left join user_stats
    on events.trusted_user_id = user_stats.trusted_user_id
  where
    events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and events.trusted_user_id is not null
    and events.bucket_day <= DATE_ADD(user_stats.first_day, interval 30 day)
    and users_stats.first_day >= '2023-10-01'
)

select
  project_id,
  'trusted_users_onboarded' as metric,
  COUNT(distinct trusted_user_id) as amount
from first_txns
group by
  project_id
