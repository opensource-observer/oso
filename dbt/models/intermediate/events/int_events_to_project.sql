{# 
  All events to a project
#}

SELECT
  a.project_id,
  e.time,
  e.event_type,
  e.to_id,
  e.from_id,
  e.amount
FROM {{ ref('int_events_with_artifact_id') }} AS e
JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a 
  ON a.artifact_source_id = e.to_source_id 
    AND a.artifact_namespace = e.to_namespace 
    AND a.artifact_type = e.to_type