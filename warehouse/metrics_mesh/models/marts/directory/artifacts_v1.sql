MODEL (
  name metrics.artifacts_v1,
  kind FULL,
  tags (
    'export'
  ),
);

select
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
from metrics.int_artifacts
