{# 
  All events to a project
#}

select
  int_artifacts_by_project.project_id,
  int_events.from_artifact_id,
  int_events.to_artifact_id,
  int_events.time,
  int_events.event_source,
  int_events.event_type,
  int_events.amount
from {{ ref('int_events') }}
inner join {{ ref('int_artifacts_by_project') }}
  on
    int_events.to_artifact_id
    = int_artifacts_by_project.artifact_id
