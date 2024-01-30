{# 
  All event by project
#}

SELECT
  a.project_slug,
  e.time,
  e.type,
  a.name as `to_name`,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  e.from_name,
  e.from_namespace,
  e.from_source_id,
  e.amount
FROM {{ ref('all_events') }} AS e
JOIN {{ ref('artifacts') }} AS a 
  ON a.source_id = e.to_source_id 
    AND a.namespace = e.to_namespace 
    AND a.type = e.to_type