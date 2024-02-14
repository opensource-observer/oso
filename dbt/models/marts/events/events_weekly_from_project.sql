{# 
  All events weekly from a project
#}

SELECT
  e.project_slug,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) as bucket_week,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_project') }} AS e
WHERE e.project_slug IS NOT NULL
GROUP BY 1,2,3