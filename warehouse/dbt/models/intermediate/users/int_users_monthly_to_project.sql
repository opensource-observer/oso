{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

with users as (
  select
    project_id,
    event_source,
    event_type,
    bucket_month,
    COUNT(distinct from_artifact_id) as amount
  from {{ ref('int_user_events_monthly_to_project') }}
  group by
    project_id,
    event_source,
    event_type,
    bucket_month
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
