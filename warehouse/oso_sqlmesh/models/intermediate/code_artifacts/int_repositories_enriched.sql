MODEL (
  name oso.int_repositories_enriched,
  description 'All repositories enriched with release and package data',
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

WITH releases AS (
  SELECT
    artifact_id AS repo_artifact_id,
    last_release_published
  FROM oso.int_latest_release_by_repo
), packages AS (
  SELECT DISTINCT
    package_github_owner,
    package_github_repo,
    COUNT(DISTINCT package_artifact_name) AS num_packages_in_deps_dev
  FROM oso.int_packages
  WHERE
    is_current_owner = TRUE
  GROUP BY
    package_github_owner,
    package_github_repo
), deps AS (
  SELECT
    dependency_artifact_id,
    COUNT(DISTINCT dependent_artifact_id) AS num_dependent_repos_in_oso
  FROM oso.int_code_dependencies
  GROUP BY
    dependency_artifact_id
)
SELECT DISTINCT
  repos.project_id,
  repos.artifact_id,
  repos.artifact_namespace,
  repos.artifact_name,
  repos.artifact_url,
  repos.is_fork,
  repos.star_count,
  repos.fork_count,
  repos.license_name,
  repos.license_spdx_id,
  repos.language,
  repos.created_at,
  repos.updated_at,
  releases.last_release_published,
  COALESCE(packages.num_packages_in_deps_dev, 0) AS num_packages_in_deps_dev,
  COALESCE(deps.num_dependent_repos_in_oso, 0) AS num_dependent_repos_in_oso
FROM oso.int_repositories AS repos
LEFT JOIN releases
  ON repos.artifact_id = releases.repo_artifact_id
LEFT JOIN packages
  ON repos.artifact_namespace = packages.package_github_owner
  AND repos.artifact_name = packages.package_github_repo
LEFT JOIN deps
  ON repos.artifact_id = deps.dependency_artifact_id