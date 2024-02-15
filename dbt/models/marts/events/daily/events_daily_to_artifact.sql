{# 
  All events daily to an artifact
#}

SELECT
  e.to_id as artifact_id,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1,2,3