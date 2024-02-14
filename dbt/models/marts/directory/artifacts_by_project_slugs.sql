SELECT
  atp.project_slug as project_slug,
  a.source_id as artifact_source_id,
  a.namespace as artifact_namespace,
  a.type as artifact_type
FROM {{ ref('artifacts') }} as a
JOIN {{ ref('stg_ossd__artifacts_to_project') }} as atp
  ON atp.source_id = a.source_id 
    AND atp.namespace = a.namespace 
    AND atp.type = a.type