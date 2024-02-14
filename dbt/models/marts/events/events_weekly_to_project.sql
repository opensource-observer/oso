{# 
  All events weekly to a project
#}

SELECT
  e.project_slug,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) as bucket_week,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_project') }} AS e
GROUP BY 1,2,3