with txns as (
  select
    project_id,
    from_artifact_name,
    bucket_day
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
),

daas as (
  select
    project_id,
    bucket_day,
    COUNT(distinct from_artifact_name) as active_addresses
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
  'daily_active_addresses' as metric,
  SUM(active_addresses) / (select days from total_days) as amount
from daas
group by
  project_id
