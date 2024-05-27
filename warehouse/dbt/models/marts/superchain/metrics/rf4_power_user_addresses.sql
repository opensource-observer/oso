with txns as (
  select
    project_id,
    from_artifact_name,
    bucket_day,
    amount
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
),

address_stats as (
  select
    from_artifact_name,
    COUNT(distinct bucket_day) as days_count,
    COUNT(distinct project_id) as project_count,
    SUM(amount) as txns_count
  from txns
  group by
    from_artifact_name
),

power_users as (
  select from_artifact_name
  from address_stats
  where
    days_count >= 30
    and project_count >= 10
    and txns_count >= 100
)

select
  txns.project_id,
  'power_user_addresses' as metric,
  COUNT(distinct txns.from_artifact_name) as amount
from txns
left join power_users
  on txns.from_artifact_name = power_users.from_artifact_name
where
  power_users.from_artifact_name is not null
group by
  txns.project_id
