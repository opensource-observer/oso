{# 
  All events to a project
#}

SELECT
  a.project_slug,
  e.time,
  e.event_type,
  -- Determine the canonical `to` artifact name. However for uniqueness we
  -- actually need to use the `to_source_id` from the `all_events` table. 
  a.artifact_name as `to_name`,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  e.from_name,
  e.from_namespace,
  e.from_type,
  e.from_source_id,
  e.amount
FROM {{ ref('int_events') }} AS e
JOIN {{ ref('stg_ossd__artifacts_to_project') }} AS a 
  ON a.artifact_source_id = e.to_source_id 
    AND a.artifact_namespace = e.to_namespace 
    AND a.artifact_type = e.to_type