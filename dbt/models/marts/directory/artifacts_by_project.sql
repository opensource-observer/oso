SELECT
  atp.project_id as project_id,
  a.artifact_id as artifact_id
FROM {{ ref('artifacts') }} as a
JOIN {{ ref('stg_ossd__artifacts_by_project') }} as atp
  ON atp.artifact_source_id = a.artifact_source_id 
    AND atp.artifact_namespace = a.artifact_namespace 
    AND atp.artifact_type = a.artifact_type