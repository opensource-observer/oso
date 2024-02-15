SELECT
  atp.project_id as project_id,
  atp.artifact_id as artifact_id
FROM {{ ref('stg_ossd__artifacts_by_project') }} as atp