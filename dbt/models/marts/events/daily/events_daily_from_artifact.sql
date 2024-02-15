{# 
  All events daily from an artifact
#}

SELECT
  e.from_id as artifact_id,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_from_project') }} AS e
GROUP BY 1,2,3