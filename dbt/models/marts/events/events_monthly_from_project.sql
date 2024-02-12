{# 
  All events monthly from a project
#}

SELECT
  e.project_slug,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) as bucket_month,
  e.type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_project') }} AS e
WHERE e.project_slug IS NOT NULL
GROUP BY 1,2,3