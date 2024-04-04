{# 
  All events weekly from a project
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) AS bucket_week,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_project') }} AS e
WHERE e.project_id IS NOT NULL
GROUP BY 1, 2, 3
