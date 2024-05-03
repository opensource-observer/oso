{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}
select
  projects_by_collection.project_id,
  projects_by_collection.project_source,
  projects_by_collection.project_namespace,
  projects_by_collection.project_name,
  collections.collection_id,
  collections.collection_source,
  collections.collection_namespace,
  collections.collection_name
from {{ ref('int_projects_by_collection') }} as projects_by_collection
left join {{ ref('int_collections') }} as collections
  on projects_by_collection.collection_id = collections.collection_id
