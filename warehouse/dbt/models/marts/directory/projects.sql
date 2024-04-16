{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  projects.id AS project_id,
  projects.slug AS project_slug,
  -- description AS project_description,
  projects.name AS project_name,
  projects.namespace AS user_namespace,
  project_owners.primary_github_owner,
  project_owners.count_github_owners,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(projects.github)) AS count_github_artifacts,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(projects.blockchain))
    AS count_blockchain_artifacts,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(projects.npm)) AS count_npm_artifacts
FROM {{ ref('stg_ossd__current_projects') }} AS projects
INNER JOIN {{ ref('int_project_owners') }} AS project_owners
  ON projects.id = project_owners.project_id
