{#
  This filters at the oss-directory level to ensure that the playground is very
  minimal. It only includes a small number of projects.
#}
{{
  config(
    materialized='table',
  ) if target.name in ['production', 'base_playground'] else config(
    enabled=false,
  )
}}
with filtered_projects as (
  select distinct 
    projects.project_name as `name`, 
    projects.sync_time as `sync_time`
  from {{ ref('stg_ossd__current_projects') }} as projects 
  inner join {{ ref("base_playground__project_filter") }} as filtered
    on filtered.project_name = projects.project_name
)

select projects.*
from {{ oso_source("ossd", "projects") }} as projects
inner join filtered_projects as filtered
  on filtered.name = projects.name
    and projects.committed_time = filtered.sync_time