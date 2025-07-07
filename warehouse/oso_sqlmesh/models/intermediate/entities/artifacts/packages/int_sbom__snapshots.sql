MODEL (
  name oso.int_sbom__snapshots,
  description 'SBOMs linked to package owner GitHub repos',
  dialect trino,
  kind FULL,
  partitioned_by (DAY("snapshot_day"), "package_source"),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

WITH sboms AS (
  SELECT DISTINCT
    DATE_TRUNC('DAY', sbom.snapshot_at) AS snapshot_day,
    sbom.artifact_source,
    sbom.artifact_namespace,
    sbom.artifact_name,
    sbom.package_source,
    sbom.package,
    sbom.package_version,
    packages.package_github_owner,
    packages.package_github_repo
  FROM oso.stg_ossd__current_sbom AS sbom
  LEFT JOIN oso.int_packages__current_maintainer_only AS packages
    ON sbom.package_source = packages.sbom_artifact_source
    AND sbom.package = packages.package_artifact_name
)

SELECT
  snapshot_day,
  artifact_source,
  artifact_namespace,
  artifact_name,
  package_source,
  package,
  package_version,
  package_github_owner,
  package_github_repo,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS dependent_repo_artifact_id,
  @oso_entity_id(artifact_source, package_github_owner, package_github_repo)
    AS dependency_repo_artifact_id,
  @oso_entity_id(package_source, '', package)
    AS dependency_package_artifact_id
FROM sboms