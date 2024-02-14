{# 
  All events daily from a project
#}

SELECT
  e.project_id,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_from_project') }} AS e
WHERE e.project_id IS NOT NULL
GROUP BY 1,2,3