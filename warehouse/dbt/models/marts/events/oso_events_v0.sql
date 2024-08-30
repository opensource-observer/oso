{#
  Grab all events associated with OSO (the project)
#}


{{ 
  config(
    materialized='table'
  )
}}

select
  int_events.time,
  int_events.event_source,
  int_events.event_source_id,
  int_events.event_type,
  int_events.to_artifact_id,
  int_events.to_artifact_namespace,
  int_events.to_artifact_name,
  int_events.to_artifact_type,
  int_events.to_artifact_source_id,
  int_events.from_artifact_id,
  int_events.from_artifact_namespace,
  int_events.from_artifact_name,
  int_events.from_artifact_type,
  int_events.from_artifact_source_id,
  int_events.amount
from {{ ref('int_events') }}
inner join {{ ref('int_artifacts_by_project') }}
  on
    int_events.to_artifact_id
    = int_artifacts_by_project.artifact_id
where int_artifacts_by_project.project_name = 'opensource-observer'
