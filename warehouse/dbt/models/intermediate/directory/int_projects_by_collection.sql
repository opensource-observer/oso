{#
  Many to many relationship table for collections
#}

select
  stg_ossd__current_collections.collection_id,
  stg_ossd__current_collections.collection_source,
  stg_ossd__current_collections.collection_namespace,
  stg_ossd__current_collections.collection_name,
  stg_ossd__current_projects.project_id,
  stg_ossd__current_projects.project_source,
  stg_ossd__current_projects.project_namespace,
  stg_ossd__current_projects.project_name
from {{ ref('stg_ossd__current_collections') }}
cross join UNNEST(stg_ossd__current_collections.projects) as project_name
inner join {{ ref('stg_ossd__current_projects') }}
  on stg_ossd__current_projects.project_name = project_name
