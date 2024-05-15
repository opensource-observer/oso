with txns as (
  select
    project_id,
    SUM(
      case
        when trusted_user_id is not null then amount
        else 0
      end
    ) as trusted_txns,
    SUM(amount) as all_txns,
    COUNT(distinct trusted_user_id) as trusted_users
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
  group by
    project_id
)

select
  project_id,
  'trusted_transaction_share' as metric,
  trusted_txns / all_txns as amount
from txns
where trusted_users >= 100
