{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  project_id,
  namespace AS user_namespace,
  project_slug,
  project_name,
  count_github_owners,
  count_github_artifacts,
  count_blockchain_artifacts,
  count_npm_artifacts
FROM {{ ref('int_projects') }}
