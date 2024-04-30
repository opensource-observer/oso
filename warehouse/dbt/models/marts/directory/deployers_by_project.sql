{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  atp.project_id AS project_id,
  atp.project_slug AS project_slug,
  atp.artifact_id AS artifact_id,
  atp.artifact_namespace AS artifact_namespace,
  atp.artifact_name AS artifact_name
FROM {{ ref('artifacts_by_project') }} AS atp
WHERE atp.artifact_type = 'DEPLOYER'
