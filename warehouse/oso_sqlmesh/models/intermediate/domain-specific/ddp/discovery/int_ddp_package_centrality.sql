MODEL (
  name oso.int_ddp_package_centrality,
  description "Metrics for package dependencies of Ethereum repositories",
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
  LEFT JOIN oso.int_ddp_repo_features AS r
    ON cd.dependent_artifact_id = r.artifact_id
    AND r.is_ethereum
  GROUP BY
    cd.package_owner_artifact_id,
    cd.package_owner_artifact_namespace,
    cd.package_owner_artifact_name
)

SELECT
  p.package_owner_artifact_id AS artifact_id,
  p.package_owner_namespace AS repo_maintainer,
  p.package_owner_name AS repo_name,
  p.num_packages AS num_packages,
  p.ethereum_dependent_repos AS ethereum_dependent_repos,
  p.all_dependent_repos AS all_dependent_repos,
  CAST(p.ethereum_dependent_repos AS DOUBLE) / NULLIF(CAST(p.all_dependent_repos AS DOUBLE), 0) AS ethereum_centrality_score,
  COALESCE(r.is_ethereum, FALSE) AS is_ethereum,
  COALESCE(r.is_in_ossd, FALSE) AS is_in_ossd,
  COALESCE(r.is_owner_in_ossd, FALSE) AS is_owner_in_ossd,
  r.last_activity_time AS last_activity_time,
  r.age_months AS age_months,
  r.contributor_count AS contributor_count,
  r.is_current_repo AS is_current_repo
FROM pkg_deps AS p
LEFT JOIN oso.int_ddp_repo_features AS r
  ON p.package_owner_artifact_id = r.artifact_id