MODEL (
  name oso.int_sbom_to_packages,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  sbom.dependent_artifact_id,
  sbom.dependent_artifact_source,
  sbom.dependent_artifact_namespace,
  sbom.dependent_artifact_name,
  packages.package_artifact_id,
  packages.package_artifact_source,
  packages.package_artifact_namespace,
  packages.package_artifact_name,
  packages.package_artifact_url,
  sbom.package_version,
  packages.package_owner_artifact_id,
  packages.package_owner_artifact_source,
  packages.package_owner_artifact_namespace,
  packages.package_owner_artifact_name,
  sbom.snapshot_at
FROM oso.int_sbom__latest_snapshot AS sbom
JOIN oso.int_packages__current_maintainer_only AS packages
  ON sbom.package_artifact_id = packages.package_artifact_id