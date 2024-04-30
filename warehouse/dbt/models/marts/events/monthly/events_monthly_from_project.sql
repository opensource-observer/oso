{# 
  All events monthly from a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_project') }} AS e
WHERE e.project_id IS NOT NULL
GROUP BY 1, 2, 3
