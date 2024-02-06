{# 
  All events from a project
#}

SELECT
  a.project_slug,
  e.time,
  e.type,
  e.to_name,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  -- Determine the canonical `from` artifact name. However for uniqueness we
  -- actually need to use the `from_source_id` from the `all_events` table. 
  CASE 
    WHEN a.name IS NULL THEN e.name 
    ELSE a.name
  END AS `from_name`,
  e.from_namespace,
  e.from_source_id,
  e.amount
FROM {{ ref('all_events') }} AS e
LEFT JOIN {{ ref('artifacts') }} AS a 
  ON a.source_id = e.from_source_id 
    AND a.namespace = e.from_namespace 
    AND a.type = e.from_type