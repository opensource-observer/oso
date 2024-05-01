{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.project_id,
  p.project_slug,
  e.from_namespace AS `from_artifact_namespace`,
  e.event_type,
  MIN(e.bucket_day) AS first_event_date,
  MAX(e.bucket_day) AS last_event_date,
  COUNT(DISTINCT e.bucket_day) AS count_days_with_event
FROM {{ ref('events_daily_to_project_by_source') }} AS e
INNER JOIN {{ ref('projects_v1') }} AS p ON p.project_id = e.project_id
GROUP BY e.project_id, p.project_slug, e.from_namespace, e.event_type
