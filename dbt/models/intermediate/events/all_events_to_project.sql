{# 
  All events to a project
#}

SELECT
  a.project_slug,
  e.time,
  e.type,
  -- Determine the canonical `to` artifact name. However for uniqueness we
  -- actually need to use the `to_source_id` from the `all_events` table. 
  a.name as `to_name`,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  e.from_name,
  e.from_namespace,
  e.from_type,
  e.from_source_id,
  e.amount
FROM {{ ref('all_events') }} AS e
JOIN {{ ref('project_artifacts') }} AS a 
  ON a.source_id = e.to_source_id 
    AND a.namespace = e.to_namespace 
    AND a.type = e.to_type