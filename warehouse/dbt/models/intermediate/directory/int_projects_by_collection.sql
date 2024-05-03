select
  projects_by_collection.collection_id,
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
from {{ ref('int_ossd__projects_by_collection') }} as projects_by_collection
inner join {{ ref('stg_ossd__current_projects') }} as projects
  on projects_by_collection.project_id = projects.project_id
