{# 
  All events weekly to a project
#}

SELECT
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) AS bucket_week,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_project') }} AS e
GROUP BY 1, 2, 3
