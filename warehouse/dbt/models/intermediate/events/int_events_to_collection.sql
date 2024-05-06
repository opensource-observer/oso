{# 
  All events to a collection
#}

select
  int_projects_by_collection.collection_id,
  int_events_to_project.project_id,
  int_events_to_project.from_artifact_id,
  int_events_to_project.to_artifact_id,
  int_events_to_project.time,
  int_events_to_project.event_source,
  int_events_to_project.event_type,
  int_events_to_project.amount
from {{ ref('int_events_to_project') }}
inner join {{ ref('int_projects_by_collection') }}
  on int_events_to_project.project_id = int_projects_by_collection.project_id
