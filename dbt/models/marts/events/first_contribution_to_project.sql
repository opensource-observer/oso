SELECT 
  e.event_type,
  e.project_slug,
  e.from_source_id,
  e.from_type,
  e.from_namespace,
  MIN(e.time) as event_time
FROM {{ ref('int_events_to_project') }} as e
GROUP BY event_type, project_slug, from_source_id, from_type, from_namespace