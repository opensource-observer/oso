{{ 
  config(meta = {
    'sync_to_db': True

  }) 
}}

{# for now this just copies all of the artifacts data #}
select
  artifact_id,
  artifact_source_id,
  artifact_namespace,
  artifact_name,
  artifact_type,
  artifact_url
from {{ ref('int_artifacts') }}
