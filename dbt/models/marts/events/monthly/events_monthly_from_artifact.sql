{# 
  All events monthly from an artifact
#}

SELECT
  e.artifact_id,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) as bucket_month,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_artifact') }} AS e
GROUP BY 1,2,3