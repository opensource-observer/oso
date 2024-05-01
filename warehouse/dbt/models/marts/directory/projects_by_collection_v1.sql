{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}
SELECT
  pbc.project_id,
  pbc.project_namespace,
  pbc.project_slug,
  pbc.project_name,
  c.collection_id,
  c.collection_namespace,
  c.collection_slug,
  c.collection_name
FROM {{ ref('int_projects_by_collection') }} AS pbc
LEFT JOIN {{ ref('collections_v1') }} AS c
  ON pbc.collection_id = c.collection_id
