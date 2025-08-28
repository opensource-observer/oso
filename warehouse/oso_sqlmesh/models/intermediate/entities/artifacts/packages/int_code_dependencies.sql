MODEL (
  name oso.int_code_dependencies,
  description 'Maps GitHub artifacts to the GitHub artifacts they depend on',
  kind VIEW,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  dependent_artifact_id,
  dependent_artifact_source,
  dependent_artifact_namespace,
  dependent_artifact_name,
  package_owner_artifact_id,
  package_owner_artifact_source,
  package_owner_artifact_namespace,
  package_owner_artifact_name,
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name
FROM oso.int_sbom_to_packages