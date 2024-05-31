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
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  project_id,
  project_source,
  project_namespace,
  project_name
from {{ ref('int_artifacts_by_project') }}
