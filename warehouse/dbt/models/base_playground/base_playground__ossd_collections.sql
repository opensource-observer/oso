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
with filtered_collections as (
  select distinct 
    collections.collection_name as `name`, 
    collections.sync_time as `sync_time`
  from {{ ref('stg_ossd__current_collections') }} as collections
  cross join UNNEST(collections.projects) as project_name
  inner join {{ ref('stg_ossd__current_projects') }} as projects
    on projects.project_name = project_name
  where project_name IN (select * from {{ ref("base_playground__project_filter") }})
)

select collections.*
from {{ oso_source("ossd", "collections") }} as collections
inner join filtered_collections as filtered
  on filtered.name = collections.name
    and collections.committed_time = filtered.sync_time