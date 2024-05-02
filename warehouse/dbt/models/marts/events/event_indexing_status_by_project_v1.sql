{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  events.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  events.from_namespace AS `artifact_source`,
  events.event_type,
  MIN(events.bucket_day) AS first_event_date,
  MAX(events.bucket_day) AS last_event_date,
  COUNT(DISTINCT events.bucket_day) AS count_days_with_event
FROM {{ ref('events_daily_to_project_by_source') }} AS events
INNER JOIN {{ ref('projects_v1') }} AS projects
  ON projects.project_id = events.project_id
GROUP BY
  events.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  events.from_namespace,
  events.event_type
