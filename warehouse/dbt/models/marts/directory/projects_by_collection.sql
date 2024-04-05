{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}
SELECT
  pbc.project_id,
  pbc.project_slug,
  pbc.project_name,
  c.collection_id,
  c.collection_slug,
  c.collection_name
FROM {{ ref('int_projects_by_collection') }} AS pbc
LEFT JOIN {{ ref('collections') }} AS c
  ON pbc.collection_id = c.collection_id
