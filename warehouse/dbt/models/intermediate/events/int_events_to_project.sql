{# 
  All events to a project
#}

SELECT
  e.*,
  a.project_id
FROM {{ ref('int_events_with_artifact_id') }} AS e
INNER JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a
  ON
    e.to_source_id = a.artifact_source_id
    AND e.to_namespace = a.artifact_namespace
    AND e.to_type = a.artifact_type
