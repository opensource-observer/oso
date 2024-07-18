{# 
  The most recent view of projects from the ossd cloudquery plugin.
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
  projects.github,
  projects.npm,
  projects.blockchain,
  projects.sha as committed_sha,
  projects.committed_time as sync_time
from {{ oso_source('ossd', 'projects') }} as projects
