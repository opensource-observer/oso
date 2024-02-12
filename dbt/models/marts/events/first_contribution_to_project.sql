SELECT 
  type,
  project_slug,
  from_source_id,
  from_type,
  from_namespace,
  MIN(time) as time
FROM {{ ref('int_events_to_project') }}
GROUP BY type, project_slug, from_source_id, from_type, from_namespace