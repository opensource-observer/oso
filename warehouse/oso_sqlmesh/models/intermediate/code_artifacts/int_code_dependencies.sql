MODEL (
  name oso.int_code_dependencies,
  description 'Maps GitHub artifacts to the GitHub artifacts they depend on',
  kind FULL
);

SELECT DISTINCT
  artifact_id AS dependent_artifact_id,
  package_github_artifact_id AS dependency_artifact_id,
  package_artifact_name AS dependency_name,
  package_artifact_source AS dependency_source
FROM oso.int_sbom_artifacts