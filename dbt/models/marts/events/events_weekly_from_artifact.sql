{# 
  All events weekly from an artifact
#}

SELECT
  e.from_namespace,
  e.from_type,
  e.from_source_id,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) as WEEK,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_artifact') }} AS e
GROUP BY 1,2,3,4,5