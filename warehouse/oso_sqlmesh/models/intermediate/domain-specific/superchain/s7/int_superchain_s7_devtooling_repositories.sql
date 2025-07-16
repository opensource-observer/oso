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
    e.to_artifact_id,
    COUNT(
      DISTINCT CASE WHEN e.event_type = 'STARRED' THEN e.from_artifact_id END
    ) AS star_count,
    COUNT(
      DISTINCT CASE WHEN e.event_type = 'FORKED' THEN e.from_artifact_id END
    ) AS fork_count
  FROM oso.int_events_daily__github AS e
  JOIN oso.int_artifacts_by_project_in_op_atlas AS app
    ON e.to_artifact_id = app.artifact_id
  WHERE
    e.bucket_day >= @event_date_threshold
    AND e.event_type IN ('STARRED', 'FORKED')
  GROUP BY e.to_artifact_id
)

SELECT DISTINCT
  @oso_entity_id('OP_ATLAS', '', app.atlas_id) AS project_id,
  repos.artifact_id AS repo_artifact_id,
  repos.artifact_namespace AS repo_artifact_namespace,
  repos.artifact_name AS repo_artifact_name,
  events.star_count,
  events.fork_count,
  repos.num_packages_in_deps_dev,
  repos.num_dependent_repos_in_oso,
  repos.is_fork,
  repos.created_at,
  repos.updated_at
FROM oso.stg_op_atlas_application AS app
JOIN oso.int_artifacts_by_project_in_op_atlas AS abp
  ON app.atlas_id = abp.atlas_id
  AND abp.artifact_source = 'GITHUB'
JOIN oso.int_repositories_enriched AS repos
  ON repos.artifact_id = abp.artifact_id
LEFT JOIN events
  ON events.to_artifact_id = repos.artifact_id
WHERE app.round_id = '7'
