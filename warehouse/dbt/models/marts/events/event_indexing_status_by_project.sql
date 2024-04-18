{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  e.project_id,
  p.project_slug,
  e.from_namespace,
  e.event_type,
  MIN(e.bucket_day) AS date_first_event,
  MAX(e.bucket_day) AS date_last_event,
  COUNT(DISTINCT e.bucket_day) AS count_days_with_event
FROM {{ ref('events_daily_to_project_by_source') }} AS e
INNER JOIN {{ ref('projects') }} AS p ON p.project_id = e.project_id
GROUP BY 1, 2, 3, 4
