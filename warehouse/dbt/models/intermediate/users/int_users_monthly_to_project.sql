{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

with users as (
  select
    project_id,
    from_namespace,
    event_type,
    bucket_month,
    COUNT(distinct from_id) as amount
  from {{ ref('int_user_events_monthly_to_project') }}
  group by 1, 2, 3, 4
)

select
  project_id,
  'Developers' as user_segment_type,
  bucket_month,
  amount
from users
where event_type = 'COMMIT_CODE'
union all
select
  project_id,
  'Active Addresses' as user_segment_type,
  bucket_month,
  amount
from users
where event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
