select distinct
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_type
from {{ ref('int_all_artifacts') }}
