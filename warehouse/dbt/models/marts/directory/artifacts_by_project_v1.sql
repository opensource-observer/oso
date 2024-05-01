{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  atp.artifact_id AS artifact_id,
  atp.artifact_namespace AS artifact_namespace,
  atp.artifact_type AS artifact_type,
  atp.artifact_name AS artifact_name,
  p.project_id,
  p.project_namespace,
  p.project_slug,
  p.project_name
FROM {{ ref('stg_ossd__artifacts_by_project') }} AS atp
LEFT JOIN {{ ref('projects_v1') }} AS p
  ON atp.project_id = p.project_id
