MODEL (
  name oso.int_superchain_s7_devtooling_repositories,
  description "All repositories eligible for measurement in the S7 devtooling round",
  kind full,
);

WITH all_projects AS (
  SELECT
    project_id,
    MAX(
      CASE WHEN collection_name = '7-1' THEN true ELSE false END
    ) as applied_to_round
  FROM oso.projects_by_collection_v1
  GROUP BY 1
),

project_repos AS (
  SELECT
    all_projects.project_id,
    abp.artifact_id AS repo_artifact_id
  FROM oso.artifacts_by_project_v1 AS abp
  JOIN all_projects
    ON abp.project_id = all_projects.project_id
  WHERE 
    abp.artifact_source = 'GITHUB'
)

SELECT DISTINCT
  project_repos.project_id,
  project_repos.repo_artifact_id,
  repos.star_count,
  repos.fork_count,
  repos.last_release_published,
  repos.num_packages_in_deps_dev,
  repos.num_dependent_repos_in_oso,
  repos.is_fork,
  repos.created_at,
  repos.updated_at
FROM project_repos
JOIN oso.int_repositories_enriched as repos
  ON project_repos.repo_artifact_id = repos.artifact_id