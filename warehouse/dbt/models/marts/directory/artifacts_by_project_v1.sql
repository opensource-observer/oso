{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_project_id': ["project_id"],
      'idx_project_name': ["project_source", "project_namespace", "project_name"],
      'idx_artifact_id': ["artifact_id"],
    }
  }) 
}}

select
  artifacts_by_project.artifact_id,
  artifacts_by_project.artifact_source_id,
  artifacts_by_project.artifact_source,
  artifacts_by_project.artifact_namespace,
  artifacts_by_project.artifact_name,
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
from {{ ref('int_artifacts_by_project') }} as artifacts_by_project
left join {{ ref('int_projects') }} as projects
  on artifacts_by_project.project_id = projects.project_id
