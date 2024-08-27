{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_collection_id': ["collection_id"],
      'idx_collection_name': ["collection_source", "collection_namespace", "collection_name"],
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
  collection_id,
  collection_source,
  collection_namespace,
  collection_name
from {{ ref('int_artifacts_by_collection') }}
