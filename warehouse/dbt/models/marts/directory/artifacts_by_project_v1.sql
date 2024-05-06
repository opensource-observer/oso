{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  artifacts_by_project.artifact_id,
  artifacts_by_project.artifact_source_id,
  artifacts_by_project.artifact_namespace,
  artifacts_by_project.artifact_name,
  artifacts_by_project.artifact_type,
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
from {{ ref('int_ossd__artifacts_by_project') }} as artifacts_by_project
left join {{ ref('int_projects') }} as projects
  on artifacts_by_project.project_id = projects.project_id
