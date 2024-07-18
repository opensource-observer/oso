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
with filtered_project_ids as (
  select distinct
    projects.project_id as `project_id`
  from {{ ref("stg_ossd__current_projects") }} as projects
  inner join {{ ref("base_playground__project_filter") }} as filtered
    on filtered.project_name = projects.project_name
), filtered_repositories as (
  select distinct 
    repos.id as `id`, 
    repos.ingestion_time as `ingestion_time`
  from {{ ref("stg_ossd__current_repositories") }} as repos
  inner join {{ ref("int_artifacts_by_project") }} as artifacts_by_project
    on CAST(repos.id as string) = artifacts_by_project.artifact_source_id
  inner join filtered_project_ids as filtered
    on artifacts_by_project.project_id = filtered.project_id
)

select 
  repos.*
from {{ oso_source("ossd", "repositories") }} as repos
inner join filtered_repositories as filtered
  on filtered.id = repos.id
    and repos.ingestion_time = filtered.ingestion_time