{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  artifacts_by_project.artifact_id,
  artifacts_by_project.artifact_namespace AS artifact_source,
  null AS artifact_namespace,
  artifacts_by_project.artifact_name,
  projects.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name
FROM {{ ref('stg_ossd__artifacts_by_project') }} AS artifacts_by_project
LEFT JOIN {{ ref('projects_v1') }} AS projects
  ON artifacts_by_project.project_id = projects.project_id
