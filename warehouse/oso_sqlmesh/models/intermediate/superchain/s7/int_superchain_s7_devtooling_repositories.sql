MODEL (
  name oso.int_superchain_s7_devtooling_repositories,
  description "All repositories eligible for measurement in the S7 devtooling round",
  dialect trino,
  kind full,
);

@DEF(event_date_threshold, DATE('2024-01-01'));

WITH s7_projects AS (
  SELECT DISTINCT project_id
  FROM oso.projects_by_collection_v1
  WHERE collection_name IN ('7-1', '7-2')
),

events AS (
  SELECT DISTINCT
    to_artifact_id,
    COUNT(DISTINCT CASE WHEN event_type = 'STARRED' THEN from_artifact_id END)
      AS star_count,
    COUNT(DISTINCT CASE WHEN event_type = 'FORKED' THEN from_artifact_id END)
      AS fork_count
  FROM oso.int_events_to_project__github
  WHERE
    "time" >= @event_date_threshold
    AND event_type IN ('STARRED', 'FORKED')
    AND event_source = 'GITHUB'
  GROUP BY 1
)

SELECT DISTINCT
  abp.project_id,
  abp.artifact_id AS repo_artifact_id,
  abp.artifact_namespace AS repo_artifact_namespace,
  abp.artifact_name AS repo_artifact_name,
  events.star_count,
  events.fork_count,
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
LEFT JOIN events
  ON abp.artifact_id = events.to_artifact_id
WHERE abp.artifact_source = 'GITHUB'