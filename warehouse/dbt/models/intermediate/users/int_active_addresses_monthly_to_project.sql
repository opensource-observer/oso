{#
  Monthly active addresses to project by network
#}


with activity as (
  select
    project_id,
    event_source,
    from_artifact_id,
    DATE_TRUNC(bucket_day, month) as bucket_month,
    (address_type = 'NEW') as is_new_user
  from {{ ref('int_addresses_daily_activity') }}
),

activity_monthly as (
  select
    project_id,
    event_source,
    from_artifact_id,
    bucket_month,
    MAX(is_new_user) as is_new_user
  from activity
  group by
    project_id,
    event_source,
    from_artifact_id,
    bucket_month
),

user_classification as (
  select
    project_id,
    event_source,
    bucket_month,
    from_artifact_id,
    case
      when is_new_user then 'NEW'
      else 'RETURNING'
    end as user_type
  from activity_monthly
)

select
  project_id,
  event_source,
  bucket_month,
  user_type,
  COUNT(distinct from_artifact_id) as amount
from user_classification
group by
  project_id,
  event_source,
  bucket_month,
  user_type
