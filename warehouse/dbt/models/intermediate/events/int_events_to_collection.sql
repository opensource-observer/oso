{# 
  All events to a collection
#}

select
  e.*,
  pbc.collection_id
from {{ ref('int_events_to_project') }} as e
inner join {{ ref('int_projects_by_collection') }} as pbc
  on e.project_id = pbc.project_id
