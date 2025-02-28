{{
  config(
    materialized='table'
  )
}}

{# 
  The most recent view of projects from the ossd dagster source.
#}

select
  {# 
    id is the SHA256 of namespace + slug. We hardcode our namespace
    "oso" for now but we are assuming we will allow users to add their on the
    OSO website
  #}
  {{ oso_id('"oso"', 'name') }} as project_id,
  "OSS_DIRECTORY" as project_source,
  "oso" as project_namespace,
  projects.name as project_name,
  projects.display_name,
  projects.description,
  projects.websites,
  projects.social,
  projects.github,
  projects.npm,
  projects.blockchain,
  projects.sha,
  projects.committed_time
from {{ oso_source('ossd', 'projects') }} as projects
