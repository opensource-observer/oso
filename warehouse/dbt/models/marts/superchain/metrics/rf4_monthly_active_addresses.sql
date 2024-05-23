with txns as (
  select
    project_id,
    from_artifact_name,
    TIMESTAMP_TRUNC(bucket_day, month) as bucket_month
  from {{ ref('rf4_events_daily_to_project') }}
  where
    event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and bucket_day >= '2023-10-01'
),

maas as (
  select
    project_id,
    bucket_month,
    COUNT(distinct from_artifact_name) as active_addresses
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
  'monthly_active_addresses' as metric,
  SUM(active_addresses) / (select months from total_months) as amount
from maas
group by
  project_id
