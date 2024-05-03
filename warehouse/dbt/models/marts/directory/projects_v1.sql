{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  projects.display_name,
  projects.description
from {{ ref('int_projects') }} as projects
