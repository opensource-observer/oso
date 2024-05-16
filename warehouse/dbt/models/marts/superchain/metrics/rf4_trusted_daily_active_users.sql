with txns as (
  select
    project_id,
    trusted_user_id,
    bucket_day
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
    and trusted_user_id is not null
),

daus as (
  select
    project_id,
    bucket_day,
    COUNT(distinct trusted_user_id) as trusted_users
  from txns
  group by
    project_id,
    bucket_day
),

total_days as (
  select DATE_DIFF(max_day, min_day, day) + 1 as days
  from (
    select
      MIN(bucket_day) as min_day,
      MAX(bucket_day) as max_day
    from txns
  )
)

select
  project_id,
  'trusted_daily_active_users' as metric,
  SUM(trusted_users) / (select days from total_days) as amount
from daus
group by
  project_id
