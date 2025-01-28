MODEL (
  name metrics.int_projects,
  description 'All projects',
  kind FULL
);

select
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name,
  description,
  @json_array_length(github) as github_artifact_count,
  @json_array_length(blockchain) as blockchain_artifact_count,
  @json_array_length(npm) as npm_artifact_count
from @oso_source('bigquery.oso.stg_ossd__current_projects')
