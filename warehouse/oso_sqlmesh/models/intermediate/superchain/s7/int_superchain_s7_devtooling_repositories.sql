MODEL (
  name oso.int_superchain_s7_devtooling_repositories,
  description "All repositories eligible for measurement in the S7 devtooling round",
  dialect trino,
  kind full,
);

WITH s7_projects AS (
  SELECT DISTINCT project_id
  FROM oso.projects_by_collection_v1
  WHERE collection_name = '7-1'
)

SELECT DISTINCT
  abp.project_id,
  abp.artifact_id AS repo_artifact_id,
  abp.artifact_namespace AS repo_artifact_namespace,
  abp.artifact_name AS repo_artifact_name,
  repos.star_count,
  repos.fork_count,
  repos.last_release_published,
  repos.num_packages_in_deps_dev,
  repos.num_dependent_repos_in_oso,
  repos.is_fork,
  repos.created_at,
  repos.updated_at
FROM oso.artifacts_by_project_v1 AS abp
JOIN s7_projects ON abp.project_id = s7_projects.project_id
LEFT JOIN oso.int_repositories_enriched repos
  ON abp.artifact_id = repos.artifact_id
WHERE abp.artifact_source = 'GITHUB'