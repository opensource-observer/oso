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
from @oso_source('bigquery.oso.artifacts_by_project_v1')
