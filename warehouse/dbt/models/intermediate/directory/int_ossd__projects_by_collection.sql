{#
  Many to many relationship table for collections
#}

select
  collections.collection_id,
  projects.project_id
from {{ ref('stg_ossd__current_collections') }} as collections
cross join UNNEST(collections.projects) as project_name
inner join {{ ref('stg_ossd__current_projects') }} as projects
  on projects.project_name = project_name
