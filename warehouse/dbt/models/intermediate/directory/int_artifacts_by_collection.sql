select distinct
  artifacts.artifact_id,
  artifacts.artifact_source_id,
  artifacts.artifact_source,
  artifacts.artifact_namespace,
  artifacts.artifact_name,
  artifacts.artifact_url,
  projects_by_collection.collection_id,
  projects_by_collection.collection_source,
  projects_by_collection.collection_namespace,
  projects_by_collection.collection_name
from {{ ref('int_all_artifacts') }} as artifacts
left join {{ ref('int_projects_by_collection') }} as projects_by_collection
  on artifacts.project_id = projects_by_collection.project_id
where projects_by_collection.collection_id is not null
