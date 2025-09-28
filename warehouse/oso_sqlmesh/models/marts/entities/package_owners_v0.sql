MODEL (
  name oso.package_owners_v0,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  package_artifact_id,
  package_artifact_source,
  package_artifact_namespace,
  package_artifact_name,
  package_owner_artifact_id,
  package_owner_artifact_source,
  package_owner_artifact_namespace,
  package_owner_artifact_name
FROM oso.int_sbom_to_packages