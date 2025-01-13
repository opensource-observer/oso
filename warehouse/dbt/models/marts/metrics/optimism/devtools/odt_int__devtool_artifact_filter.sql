{% set max_release_date_months = 6 %}

with eligible_projects as (
  select
    to_artifact_id as artifact_id,
    max(time) as last_release_date
  from {{ ref('int_events__github') }}
  where event_type = 'RELEASE_PUBLISHED'
  group by to_artifact_id
)

select artifact_id
from eligible_projects
where last_release_date >= date_sub(
  current_date(), interval {{ max_release_date_months }} month
)
