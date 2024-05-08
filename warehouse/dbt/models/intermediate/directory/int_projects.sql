select
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name,
  description,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(github))
    as github_artifact_count,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(blockchain))
    as blockchain_artifact_count,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(npm))
    as npm_artifact_count
from {{ ref('stg_ossd__current_projects') }}
