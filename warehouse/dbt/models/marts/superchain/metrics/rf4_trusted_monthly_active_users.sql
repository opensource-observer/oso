with txns as (
  select
    project_id,
    trusted_user_id,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
    and trusted_user_id is not null
),

maus as (
  select
    project_id,
    bucket_month,
    COUNT(distinct trusted_user_id) as trusted_users
  from txns
  group by
    project_id,
    bucket_month
),

total_months as (
  select
    {# TODO: double check this math #}
    (DATE_DIFF(max_month, min_month, day) + 30) / 30 as months
  from (
    select
      MIN(bucket_month) as min_month,
      MAX(bucket_month) as max_month
    from txns
  )
)

select
  project_id,
  'trusted_monthly_active_users' as metric,
  SUM(trusted_users) / (select months from total_months) as amount
from maus
group by
  project_id
