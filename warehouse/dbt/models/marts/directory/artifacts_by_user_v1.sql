{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_user_id': ["user_id"],
      'idx_user_name': ["user_source", "user_namespace", "user_name"],
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
  user_id,
  user_source_id,
  user_source,
  user_type,
  user_namespace,
  user_name
from {{ ref('int_artifacts_by_user') }}
