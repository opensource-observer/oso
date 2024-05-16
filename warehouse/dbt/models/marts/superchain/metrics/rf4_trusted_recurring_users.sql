with txns as (
  select
    project_id,
    trusted_user_id,
    bucket_day,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
    and trusted_user_id is not null
),

user_stats as (
  select
    project_id,
    trusted_user_id,
    COUNT(distinct bucket_month) as months,
    MAX(bucket_day) as last_day
  from txns
  group by
    project_id,
    trusted_user_id
)

select
  project_id,
  'trusted_recurring_users' as metric,
  COUNT(distinct trusted_user_id) as amount
from user_stats
where
  months >= 3
  and last_day >= '2024-04-01'
group by
  project_id
