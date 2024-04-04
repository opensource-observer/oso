{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  id AS project_id,
  slug AS project_slug,
  -- description AS project_description,
  name AS project_name,
  namespace AS user_namespace,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(github)) AS count_github_artifacts,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(blockchain)) AS count_blockchain_artifacts,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(npm)) AS count_npm_artifacts
FROM {{ ref('stg_ossd__current_projects') }}
