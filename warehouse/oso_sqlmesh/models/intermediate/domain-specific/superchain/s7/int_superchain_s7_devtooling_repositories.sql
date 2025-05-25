MODEL (
  name oso.int_superchain_s7_devtooling_repositories,
  description "All repositories eligible for measurement in the S7 devtooling round",
  dialect trino,
  kind full,
  tags (
    'entity_category=project',
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

@DEF(event_date_threshold, DATE('2024-01-01'));

WITH events AS (
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
  app.project_id,
  repos.artifact_id AS repo_artifact_id,
  repos.artifact_namespace AS repo_artifact_namespace,
  repos.artifact_name AS repo_artifact_name,
  events.star_count,
  events.fork_count,
  repos.last_release_published,
  repos.num_packages_in_deps_dev,
  repos.num_dependent_repos_in_oso,
  repos.is_fork,
  repos.created_at,
  repos.updated_at
FROM oso.stg_op_atlas_application AS app
JOIN oso.stg_op_atlas_project_repository AS pr
  ON app.project_id = pr.project_id
JOIN oso.int_repositories_enriched AS repos
  ON repos.artifact_namespace = pr.artifact_namespace
  AND repos.artifact_name = pr.artifact_name
LEFT JOIN events
  ON events.to_artifact_id = repos.artifact_id
WHERE app.round_id = '7'
