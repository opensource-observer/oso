{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_artifact_id': ["artifact_id"],
      'idx_artifact_name': ["artifact_source", "artifact_namespace", "artifact_name"],
    }
  }) 
}}

{# for now this just copies all of the artifacts data #}
select
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url
from {{ ref('int_artifacts') }}
