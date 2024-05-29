{{ 
  config(meta = {
    'sync_to_db': True
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
