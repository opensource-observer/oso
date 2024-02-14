SELECT 
  e.event_type,
  e.project_slug,
  e.from_source_id as artifact_source_id,
  e.from_type as artifact_type,
  e.from_namespace as artifact_namespace,
  MIN(e.time) as event_time
FROM {{ ref('int_events_to_project') }} as e
GROUP BY 1,2,3,4,5