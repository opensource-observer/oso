{# 
  All events from a collection
#}

select
  e.*,
  pbc.collection_id
from {{ ref('int_events_from_project') }} as e
left join {{ ref('int_projects_by_collection') }} as pbc
  on e.project_id = pbc.project_id
