MODEL (
  name oso.int_packages,
  kind FULL,
  dialect duckdb,
  audits (
    number_of_rows(threshold := 0)
  )
);

@DEF(oldest_snapshot_date, '2025-03-01');

WITH deps_dev AS (
  SELECT
    version AS package_version,
    UPPER(system) AS package_artifact_source,
    LOWER(name) AS package_artifact_name,
    LOWER(STR_SPLIT(project_name, '/')[@array_index(0)]) AS package_github_owner,
    LOWER(STR_SPLIT(project_name, '/')[@array_index(1)]) AS package_github_repo
  FROM oso.stg_deps_dev__packages
), latest_versions AS (
  SELECT
    package_artifact_source,
    package_artifact_name,
    package_github_owner AS current_owner,
    package_github_repo AS current_repo
  FROM deps_dev
  QUALIFY
    ROW_NUMBER() OVER (PARTITION BY package_artifact_name, package_artifact_source ORDER BY package_version DESC) = 1
)
SELECT
  deps_dev.package_artifact_source,
  deps_dev.package_artifact_name,
  deps_dev.package_version,
  deps_dev.package_github_owner,
  deps_dev.package_github_repo,
  CASE
    WHEN deps_dev.package_artifact_source = 'CARGO'
    THEN 'RUST'
    WHEN deps_dev.package_artifact_source = 'NPM'
    THEN 'NPM'
    WHEN deps_dev.package_artifact_source = 'PYPI'
    THEN 'PIP'
    WHEN deps_dev.package_artifact_source = 'GO'
    THEN 'GO'
    WHEN deps_dev.package_artifact_source = 'MAVEN'
    THEN 'MAVEN'
    WHEN deps_dev.package_artifact_source = 'NUGET'
    THEN 'NUGET'
    ELSE 'UNKNOWN'
  END AS sbom_artifact_source,
  (
    deps_dev.package_github_owner = latest_versions.current_owner
    AND deps_dev.package_github_repo = latest_versions.current_repo
  ) AS is_current_owner
FROM deps_dev
LEFT JOIN latest_versions
  ON deps_dev.package_artifact_source = latest_versions.package_artifact_source
  AND deps_dev.package_artifact_name = latest_versions.package_artifact_name