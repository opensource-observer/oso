{% set max_release_lookback_days = 180 %}

with eligible_projects as (
  select
    to_artifact_id as artifact_id,
    max(time) as last_release_date
  from {{ ref('int_events__github') }}
  where event_type = 'RELEASE_PUBLISHED'
  group by to_artifact_id
),

union_all_artifacts as (
  select artifact_id
  from eligible_projects
  where
    date(last_release_date) >= date_sub(
      current_date(), interval {{ max_release_lookback_days }} day
    )
  union all
  select package_owner_artifact_id as artifact_id
  from {{ ref('package_owners_v0') }}
)

select distinct artifact_id
from union_all_artifacts
