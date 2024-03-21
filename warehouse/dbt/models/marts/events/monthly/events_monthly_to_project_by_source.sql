{# 
  All events monthly to a project by source
#}

SELECT
  e.project_id,
  e.from_id,  
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_project_by_source') }} AS e
GROUP BY 1, 2, 3, 4
