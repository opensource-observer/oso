MODEL (
  name oso.int_projects_to_projects,
  description 'Many to many mapping of OSSD defined projects to externally defined projects',
  dialect trino,
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH artifacts_by_project_source AS (
  SELECT
    directory.project_id AS ossd_project_id,
    directory.project_source AS ossd_project_source,
    directory.project_namespace AS ossd_project_namespace,
    directory.project_name AS ossd_project_name,
    ossd_projects.display_name AS ossd_display_name,
    external.project_id AS external_project_id,
    external.project_source AS external_project_source,
    external.project_namespace AS external_project_namespace,
    external.project_name AS external_project_name,
    external_projects.display_name AS external_display_name,
    directory.artifact_id
  FROM oso.int_artifacts_by_project AS directory
  JOIN oso.int_artifacts_by_project AS external
    ON directory.artifact_id = external.artifact_id
    AND directory.project_source = 'OSS_DIRECTORY'
    AND external.project_source != 'OSS_DIRECTORY'
    AND directory.project_id != external.project_id
  JOIN oso.int_projects AS ossd_projects
    ON directory.project_id = ossd_projects.project_id
  JOIN oso.int_projects AS external_projects
    ON external.project_id = external_projects.project_id
)

SELECT DISTINCT
  ossd_project_id,
  ossd_project_source,
  ossd_project_namespace,
  ossd_project_name,
  ossd_display_name,
  external_project_id,
  external_project_source,
  external_project_namespace,
  external_project_name,
  external_display_name,
  artifact_id
FROM artifacts_by_project_source
