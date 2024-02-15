SELECT 
  e.event_type,
  e.project_id,
  e.from_id as artifact_id,
  MAX(e.time) as event_time
FROM {{ ref('int_events_to_project') }} as e
GROUP BY 1,2,3