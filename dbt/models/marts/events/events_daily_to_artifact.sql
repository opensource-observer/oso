{# 
  All events daily to an artifact
#}

SELECT
  e.to_namespace as artifact_namespace,
  e.to_type as artifact_type,
  e.to_source_id as artifact_source_id,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1,2,3,4,5