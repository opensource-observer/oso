MODEL (
  name metrics.artifacts_by_user_v1,
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
  user_id,
  user_source_id,
  user_source,
  user_type,
  user_namespace,
  user_name
from metrics.int_artifacts_by_user