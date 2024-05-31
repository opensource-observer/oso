{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_project_id': ["project_id"],
      'idx_project_name': ["project_source", "project_namespace", "project_name"],
    }
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
