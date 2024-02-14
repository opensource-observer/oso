{# 
  All events from a project
#}

SELECT
  a.project_slug,
  e.time,
  e.event_type,
  e.to_name,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  -- Determine the canonical `from` artifact name. However for uniqueness we
  -- actually need to use the `from_source_id` from the `all_events` table. 
  CASE 
    WHEN a.artifact_name IS NULL THEN e.from_name 
    ELSE a.artifact_name
  END AS `from_name`,
  e.from_namespace,
  e.from_type,
  e.from_source_id,
  e.amount
FROM {{ ref('int_events') }} AS e
LEFT JOIN {{ ref('stg_ossd__artifacts_to_project') }} AS a 
  ON a.artifact_source_id = e.from_source_id 
    AND a.artifact_namespace = e.from_namespace 
    AND a.artifact_type = e.from_type