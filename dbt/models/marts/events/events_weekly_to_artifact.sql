{# 
  All events weekly to an artifact
#}

SELECT
  e.artifact_namespace as artifact_namespace,
  e.artifact_type as artifact_type,
  e.artifact_source_id as artifact_source_id,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) as bucket_week,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_artifact') }} AS e
GROUP BY 1,2,3,4,5