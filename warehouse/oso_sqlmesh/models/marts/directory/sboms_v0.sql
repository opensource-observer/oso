MODEL (
  name oso.sboms_v0,
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT DISTINCT
  project_id AS from_project_id,
  artifact_id AS from_artifact_id,
  artifact_source AS from_artifact_source,
  artifact_namespace AS from_artifact_namespace,
  artifact_name AS from_artifact_name,
  package_project_id AS to_package_project_id,
  package_artifact_id AS to_package_artifact_id,
  package_artifact_source AS to_package_artifact_source,
  package_artifact_namespace AS to_package_artifact_namespace,
  package_artifact_name AS to_package_artifact_name
FROM oso.int_sbom_artifacts