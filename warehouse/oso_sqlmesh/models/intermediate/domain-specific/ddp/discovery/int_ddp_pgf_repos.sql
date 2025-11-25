MODEL (
  name oso.int_ddp_pgf_repos,
  description "Repositories that have Public Goods Funding from Ethereum partners",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH funded_projects AS (
  SELECT DISTINCT project_id
  FROM oso.timeseries_metrics_by_project_v0
  JOIN oso.projects_v1 USING project_id
  JOIN oso.metrics_v0 USING metric_id
  WHERE
    metric_model LIKE 'funding_awarded'
    AND project_source = 'OSS_DIRECTORY'
    AND metric_time_aggregation = 'over_all_time'
    AND metric_event_source IN (
      'OCTANT',
      'OPTIMISM_GOVGRANTS',
      'ARBITRUMFOUNDATION',
      'OPTIMISM_RETROFUNDING',
      'CLRFUND',
      'GITCOIN_MATCHING',
      'GITCOIN_DONATIONS'
    )
    AND amount >= 5000
  GROUP BY 1
),
project_repos AS (
  SELECT
    artifact_id,
    project_id
  FROM oso.artifacts_by_project_v1
  JOIN funded_projects USING project_id
  WHERE artifact_source = 'GITHUB'
),
selected_repos AS (
  SELECT
    artifact_id,
    last_artifact_id,
    project_id
  FROM oso.int_ddp_repo_lineage
  JOIN project_repos USING artifact_id
),
all_repos AS (
  SELECT
    artifact_id,
    project_id
  FROM selected_repos
  UNION ALL
  SELECT
    last_artifact_id AS artifact_id,
    project_id
  FROM selected_repos
  WHERE last_artifact_id IS NOT NULL
),
unique_repos AS (
  SELECT DISTINCT
    artifact_id,
    project_id
  FROM all_repos
)
SELECT
  artifact_id,
  artifact_namespace,
  artifact_name,
  'https://github.com/' || artifact_namespace || '/' || artifact_name AS artifact_url,
  is_current_url,
  project_id
FROM unique_repos
JOIN oso.int_ddp_repo_lineage USING artifact_id