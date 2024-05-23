with txns as (
  select
    project_id,
    from_artifact_name,
    bucket_day,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
),

address_stats as (
  select
    project_id,
    from_artifact_name,
    COUNT(distinct bucket_month) as months,
    MAX(bucket_day) as last_day
  from txns
  group by
    project_id,
    from_artifact_name
)

select
  project_id,
  'recurring_addresses' as metric,
  COUNT(distinct from_artifact_name) as amount
from address_stats
where
  months >= 3
  -- and last_day >= '2024-04-01'
group by
  project_id
