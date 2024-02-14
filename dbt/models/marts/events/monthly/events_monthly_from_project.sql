{# 
  All events monthly from a project
#}

SELECT
  e.project_id,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) as bucket_month,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_project') }} AS e
WHERE e.project_id IS NOT NULL
GROUP BY 1,2,3