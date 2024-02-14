SELECT
  atp.project_slug as project_slug,
  a.artifact_source_id as artifact_source_id,
  a.artifact_namespace as artifact_namespace,
  a.artifact_type as artifact_type
FROM {{ ref('artifacts') }} as a
JOIN {{ ref('stg_ossd__artifacts_to_project') }} as atp
  ON atp.source_id = a.source_id 
    AND atp.namespace = a.namespace 
    AND atp.type = a.type