{# 
  All events to a project
#}

select
  int_artifacts_by_project.project_id,
  int_events_with_artifact_id.from_artifact_id,
  int_events_with_artifact_id.to_artifact_id,
  int_events_with_artifact_id.time,
  int_events_with_artifact_id.event_source,
  int_events_with_artifact_id.event_type,
  int_events_with_artifact_id.amount
from {{ ref('int_events_with_artifact_id') }}
inner join {{ ref('int_artifacts_by_project') }}
  on
    int_events_with_artifact_id.to_artifact_id
    = int_artifacts_by_project.artifact_id
