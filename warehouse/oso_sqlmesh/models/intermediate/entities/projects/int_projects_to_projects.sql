MODEL (
  name oso.int_projects_to_projects,
  description 'Many to many mapping of OSSD defined projects to externally defined projects',
  dialect trino,
  kind FULL,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


WITH ossd_artifacts AS (
  SELECT
    project_id AS ossd_project_id,
    artifact_id AS shared_artifact_id,
    CASE
      WHEN artifact_type IN ('EOA', 'DEPLOYER', 'CONTRACT', 'BRIDGE') THEN 'ADDRESS'
      ELSE artifact_type
    END AS shared_artifact_type
  FROM oso.int_artifacts_by_project_in_ossd
  WHERE artifact_type IN (
    'REPOSITORY',
    'EOA',
    'DEPLOYER',
    'CONTRACT',
    'BRIDGE',
    'DEFILLAMA_PROTOCOL'
  )
),

external_artifacts AS (
  SELECT
    artifact_id AS shared_artifact_id,
    project_id AS external_project_id
  FROM oso.int_artifacts_by_project_in_op_atlas
  WHERE artifact_id IN (SELECT shared_artifact_id FROM ossd_artifacts)
)

SELECT DISTINCT
  ossd_artifacts.ossd_project_id,
  ossd_projects.project_name AS ossd_project_name,
  ossd_projects.display_name AS ossd_display_name,
  external_artifacts.external_project_id,
  external_projects.project_name AS external_project_name,
  external_projects.display_name AS external_display_name,
  external_projects.project_source AS external_project_source,
  external_projects.project_namespace AS external_project_namespace,
  ossd_artifacts.shared_artifact_id,
  ossd_artifacts.shared_artifact_type
FROM external_artifacts
JOIN ossd_artifacts
  ON external_artifacts.shared_artifact_id = ossd_artifacts.shared_artifact_id
JOIN oso.projects_v1 AS ossd_projects
  ON ossd_artifacts.ossd_project_id = ossd_projects.project_id
JOIN oso.projects_v1 AS external_projects
  ON external_artifacts.external_project_id = external_projects.project_id
