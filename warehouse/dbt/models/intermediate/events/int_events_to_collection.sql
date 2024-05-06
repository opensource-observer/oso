{# 
  All events to a collection
#}

select
  pbc.collection_id,
  a.project_id,
  e.from_artifact_id,
  e.to_artifact_id,
  e.time,
  e.event_source,
  e.event_type,
  e.amount
from {{ ref('int_events_to_project') }} as e
inner join {{ ref('int_projects_by_collection') }} as pbc
  on e.project_id = pbc.project_id
