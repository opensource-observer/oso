{# 
  All events monthly to an artifact by source
#}

SELECT
  e.artifact_id,
  e.from_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_artifact_by_source') }} AS e
GROUP BY 1, 2, 3, 4
