MODEL (
  name oso.int_ddp_package_maintainers,
  description "Package maintainers for Ethereum repositories",
  kind FULL,
  dialect trino,
  grain (artifact_id, repo_maintainer, repo_name),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH pkg_deps AS (
  SELECT
    cd.package_owner_artifact_id AS package_owner_artifact_id,
    cd.package_owner_artifact_namespace AS package_owner_namespace,
    cd.package_owner_artifact_name AS package_owner_name,
    COUNT(DISTINCT cd.package_artifact_id) AS num_packages,
    COUNT(DISTINCT CASE WHEN r.artifact_id IS NOT NULL THEN cd.dependent_artifact_id END) AS ethereum_dependent_repos,
    COUNT(DISTINCT cd.dependent_artifact_id) AS all_dependent_repos
  FROM oso.int_code_dependencies AS cd
  LEFT JOIN oso.int_ddp_repo_metadata AS r
    ON cd.dependent_artifact_id = r.artifact_id
    AND r.is_ethereum
  GROUP BY
    cd.package_owner_artifact_id,
    cd.package_owner_artifact_namespace,
    cd.package_owner_artifact_name
)

SELECT
  package_owner_artifact_id AS artifact_id,
  package_owner_namespace AS artifact_namespace,
  package_owner_name AS artifact_name,
  'https://github.com/' || package_owner_namespace || '/' || package_owner_name AS artifact_url,
  num_packages,
  ethereum_dependent_repos,
  all_dependent_repos,
  CAST(ethereum_dependent_repos AS DOUBLE) / NULLIF(CAST(all_dependent_repos AS DOUBLE), 0) AS ethereum_dependency_score
FROM pkg_deps