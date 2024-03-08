SELECT
  atp.project_id AS project_id,
  atp.artifact_id AS artifact_id
FROM {{ ref('stg_ossd__artifacts_by_project') }} AS atp
