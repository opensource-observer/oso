select
  project_id,
  'trusted_transaction_count' as metric,
  SUM(amount) as amount
from {{ ref('rf4_events_daily_to_project') }}
where
  event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
  and bucket_day >= '2023-10-01'
  and is_from_trusted_user is true
group by
  project_id
