{# 
  All events daily to a project
#}

SELECT
  e.project_slug,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1,2,3
