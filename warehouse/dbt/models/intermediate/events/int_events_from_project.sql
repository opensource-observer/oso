{# 
  All events from a project
#}

SELECT
  e.*,
  a.project_id
FROM {{ ref('int_events_with_artifact_id') }} AS e
LEFT JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a
  ON
    e.from_source_id = a.artifact_source_id
    AND e.from_namespace = a.artifact_namespace
    AND e.from_type = a.artifact_type
