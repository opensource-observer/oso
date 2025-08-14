MODEL (
  name oso.int_packages,
  kind FULL,
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

/* TODO: Need a more robust way to order packages by semantic versioning */

-- Extract and clean package data from staging
WITH raw_packages AS (
  SELECT
    version AS package_version,
    system AS package_artifact_source,
    name AS package_artifact_name,
    STR_SPLIT(project_name, '/')[@array_index(0)] AS package_github_owner,
    STR_SPLIT(project_name, '/')[@array_index(1)] AS package_github_repo
  FROM oso.stg_deps_dev__packages
),

-- Map package sources to SBOM artifact sources
package_source_mapping AS (
  SELECT
    package_artifact_source,
    package_artifact_name,
    package_version,
    package_github_owner,
    package_github_repo,
    CASE
      WHEN package_artifact_source = 'CARGO' THEN 'RUST'
      WHEN package_artifact_source = 'PYPI' THEN 'PIP'
      ELSE package_artifact_source
    END AS sbom_artifact_source,
    CASE
      WHEN package_artifact_source = 'NPM' THEN 'https://www.npmjs.com/package/' || package_artifact_name
      WHEN package_artifact_source = 'PYPI' THEN 'https://pypi.org/project/' || package_artifact_name
      WHEN package_artifact_source = 'CARGO' THEN 'https://crates.io/crates/' || package_artifact_name
      WHEN package_artifact_source = 'GO' THEN 'https://pkg.go.dev/' || package_artifact_name
      WHEN package_artifact_source = 'MAVEN' THEN 'https://mvnrepository.com/artifact/' || REPLACE(package_artifact_name, ':', '/')
      WHEN package_artifact_source = 'NUGET' THEN 'https://www.nuget.org/packages/' || package_artifact_name
      ELSE NULL
    END AS package_url
  FROM raw_packages
),

-- Find the latest version for each package to determine current ownership
latest_versions AS (
  SELECT
    package_artifact_source,
    package_artifact_name,
    package_github_owner AS current_owner,
    package_github_repo AS current_repo
  FROM package_source_mapping
  -- TODO: Should sort by semantic versioning
  QUALIFY
    ROW_NUMBER() OVER (PARTITION BY package_artifact_name, package_artifact_source ORDER BY package_version DESC) = 1
)

-- Final output with all package information
SELECT
  p.package_artifact_source,
  p.package_artifact_name,
  p.package_version,
  p.package_github_owner,
  p.package_github_repo,
  p.sbom_artifact_source,
  p.package_url,
  (
    p.package_github_owner = lv.current_owner
    AND p.package_github_repo = lv.current_repo
  ) AS is_current_owner
FROM package_source_mapping AS p
LEFT JOIN latest_versions AS lv
  ON p.package_artifact_source = lv.package_artifact_source
  AND p.package_artifact_name = lv.package_artifact_name