with transactions_std as (
  select
    project_id,
    SUM(amount) as amount
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
  group by
    project_id
),

transactions_4337 as (
  select
    project_id,
    SUM(amount) as amount
  from {{ ref('rf4_4337_events') }}
  where
    event_type = '4337_INTERACTION'
    and bucket_day >= '2023-10-01'
  group by
    project_id
),

transactions as (
  select
    project_id,
    amount
  from transactions_std
  union all
  select
    project_id,
    amount
  from transactions_4337
)

select
  project_id,
  'transaction_count' as metric,
  SUM(amount) as amount
from transactions
group by
  project_id
