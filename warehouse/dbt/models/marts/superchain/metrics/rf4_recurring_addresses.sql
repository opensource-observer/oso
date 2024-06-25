with transactions_std as (
  select
    bucket_day,
    project_id,
    from_artifact_name as address,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
),

transactions_4337 as (
  select
    bucket_day,
    project_id,
    to_artifact_name as address,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('rf4_4337_events') }}
  where
    event_type = '4337_INTERACTION'
    and bucket_day >= '2023-10-01'
),

txns as (
  select * from transactions_std
  union all
  select * from transactions_4337
),

address_stats as (
  select
    project_id,
    address,
    COUNT(distinct bucket_month) as months,
    MAX(bucket_day) as last_day
  from txns
  group by
    project_id,
    address
)

select
  project_id,
  'recurring_addresses' as metric,
  COUNT(distinct address) as amount
from address_stats
where
  months >= 3
  -- and last_day >= '2024-04-01'
group by
  project_id
