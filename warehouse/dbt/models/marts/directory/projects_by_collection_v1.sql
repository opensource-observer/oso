{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}
SELECT
  projects_by_collection.project_id,
  "OSS_DIRECTORY" AS project_source,
  projects_by_collection.project_namespace,
  projects_by_collection.project_slug AS project_name,
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name
FROM {{ ref('int_projects_by_collection') }} AS projects_by_collection
LEFT JOIN {{ ref('collections_v1') }} AS collections
  ON projects_by_collection.collection_id = collections.collection_id
