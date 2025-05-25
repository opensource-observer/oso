MODEL (
  name oso.package_owners_v0,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  package_project_id,
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name,
  package_github_project_id AS package_owner_project_id,
  package_github_artifact_id AS package_owner_artifact_id,
  package_owner_source,
  package_github_owner AS package_owner_artifact_namespace,
  package_github_repo AS package_owner_artifact_name
FROM oso.int_sbom_artifacts