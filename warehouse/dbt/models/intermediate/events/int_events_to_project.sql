{# 
  All events to a project
#}

select
  a.project_id,
  e.from_artifact_id,
  e.to_artifact_id,
  e.time,
  e.event_source,
  e.event_type,
  e.amount
from {{ ref('int_events_with_artifact_id') }} as e
inner join {{ ref('int_ossd__artifacts_by_project') }} as a
  on e.to_artifact_id = a.artifact_id
