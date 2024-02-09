SELECT 
  type,
  project_slug,
  from_source_id,
  from_type,
  from_namespace,
  MAX(time) as time
FROM {{ ref('all_events_to_project') }}
GROUP BY type, project_slug, from_source_id, from_type, from_namespace