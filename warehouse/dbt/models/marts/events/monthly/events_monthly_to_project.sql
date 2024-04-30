{# 
  All events monthly to a project
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
FROM {{ ref('events_daily_to_project') }} AS e
GROUP BY 1, 2, 3
