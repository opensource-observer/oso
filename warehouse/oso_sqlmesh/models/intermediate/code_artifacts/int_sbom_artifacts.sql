MODEL (
  name oso.int_sbom_artifacts,
  kind FULL
);

WITH ranked_snapshots AS (
  SELECT
    artifact_source,
    package_source,
    package_version,
    snapshot_at,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    LOWER(package) AS package,
    ROW_NUMBER() OVER (PARTITION BY artifact_source, artifact_namespace, artifact_name, package_source, package, package_version ORDER BY snapshot_at ASC) AS row_num
  FROM @oso_source('bigquery.ossd.sbom')
), sbom_artifacts AS (
  SELECT
    artifact_source,
    artifact_namespace,
    artifact_name,
    package_source,
    package,
    package_version,
    snapshot_at
  FROM ranked_snapshots
  WHERE
    row_num = 1
), deps_dev_packages AS (
  SELECT DISTINCT
    sbom_artifact_source,
    package_artifact_name,
    package_github_owner,
    package_github_repo
  FROM oso.int_packages
  WHERE
    is_current_owner = TRUE
)
SELECT
  all_repos.project_id, /*
    Because we use repo.id as the artifact_source_id for github, we need to lookup the artifact_id for the SBOM repo. If the artifact is not found, this will return null.
  */
  all_repos.artifact_id,
  sbom_artifacts.artifact_source,
  sbom_artifacts.artifact_namespace,
  sbom_artifacts.artifact_name,
  all_packages.project_id AS package_project_id, /*
    Because we only index packages that are found in OSSD, most of the time this will return a null package_artifact_id.
  */
  all_packages.artifact_id AS package_artifact_id,
  sbom_artifacts.package_source AS package_artifact_source,
  '' AS package_artifact_namespace,
  sbom_artifacts.package AS package_artifact_name,
  'GITHUB' AS package_owner_source,
  sbom_artifacts.package_version AS package_version,
  deps_dev_packages.package_github_owner,
  deps_dev_packages.package_github_repo,
  deps_dev_repos.artifact_id AS package_github_artifact_id,
  deps_dev_repos.project_id AS package_github_project_id,
  sbom_artifacts.snapshot_at
FROM sbom_artifacts
LEFT OUTER JOIN oso.int_all_artifacts AS all_repos
  ON sbom_artifacts.artifact_namespace = all_repos.artifact_namespace
  AND sbom_artifacts.artifact_name = all_repos.artifact_name
LEFT OUTER JOIN oso.int_all_artifacts AS all_packages
  ON sbom_artifacts.package = all_packages.artifact_name
  AND sbom_artifacts.package_source = all_packages.artifact_source
LEFT OUTER JOIN deps_dev_packages
  ON sbom_artifacts.package_source = deps_dev_packages.sbom_artifact_source
  AND sbom_artifacts.package = deps_dev_packages.package_artifact_name
LEFT OUTER JOIN oso.int_all_artifacts AS deps_dev_repos
  ON deps_dev_packages.package_github_owner = deps_dev_repos.artifact_namespace
  AND deps_dev_packages.package_github_repo = deps_dev_repos.artifact_name