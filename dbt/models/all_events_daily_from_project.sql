{# 
  All events daily from a project
#}

SELECT
  e.project_slug,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.type,
  SUM(e.amount) AS amount
FROM {{ ref('all_events_from_project') }} AS e
WHERE e.project_slug IS NOT NULL
GROUP BY 1,2,3