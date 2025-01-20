MODEL (
  name metrics.int_artifacts,
  description 'All artifacts',
  kind FULL,
);

select distinct
  artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
from metrics.int_artifacts_by_project
