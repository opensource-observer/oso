MODEL (
  name oso.int_sbom_to_packages,
  kind VIEW,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH sbom_with_project_ids AS (
  SELECT
    all_repos.project_id AS dependent_project_id,
    sbom.dependent_artifact_id,
    sbom.dependent_artifact_source,
    sbom.dependent_artifact_namespace,
    sbom.dependent_artifact_name,
    sbom.package_artifact_id,
    sbom.package_artifact_source,
    sbom.package_artifact_namespace,
    sbom.package_artifact_name,
    sbom.package_version
  FROM oso.int_sbom__latest_snapshot AS sbom
  JOIN oso.int_artifacts_by_project AS all_repos
    ON sbom.dependent_artifact_id = all_repos.artifact_id
), 
packages_with_project_ids AS (
  SELECT
    all_repos.project_id AS package_owner_project_id,
    p.package_owner_artifact_id,
    p.package_owner_artifact_source,
    p.package_owner_artifact_namespace,
    p.package_owner_artifact_name,
    p.package_artifact_id,
    p.package_artifact_source,
    p.package_artifact_namespace,
    p.package_artifact_name,
    p.package_artifact_url
  FROM oso.int_packages__current_maintainer_only AS p
  LEFT JOIN oso.int_artifacts_by_project AS all_repos
    ON p.package_artifact_id = all_repos.artifact_id
)

SELECT
  sbom.dependent_project_id,
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
  packages.package_owner_project_id,
  packages.package_owner_artifact_id,
  packages.package_owner_artifact_source,
  packages.package_owner_artifact_namespace,
  packages.package_owner_artifact_name
FROM sbom_with_project_ids AS sbom
LEFT JOIN packages_with_project_ids AS packages
  ON sbom.package_artifact_id = packages.package_artifact_id