MODEL (
  name oso.int_ddp_pgf_repos,
  description "Repositories that have Public Goods Funding from Ethereum partners",
  kind FULL,
  dialect trino,
  grain (artifact_id, project_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH funded_projects AS (
  SELECT
    project_id,
    ARRAY_AGG(DISTINCT metric_event_source) AS project_funding_sources,
    SUM(amount) AS project_total_funding
  FROM oso.timeseries_metrics_by_project_v0
  JOIN oso.projects_v1 USING project_id
  JOIN oso.metrics_v0 USING metric_id
  WHERE
    metric_model = 'funding_awarded'
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
  GROUP BY 1
),
project_repos AS (
  SELECT
    artifact_id,
    artifact_namespace,
    artifact_name,
    'https://github.com/' || artifact_namespace || '/' || artifact_name AS artifact_url,
    project_id,
    project_name
  FROM oso.artifacts_by_project_v1
  JOIN funded_projects USING project_id
  WHERE artifact_source = 'GITHUB'
)

SELECT
  artifact_id,
  artifact_namespace,
  artifact_name,
  artifact_url,
  project_id,
  project_name,
  project_funding_sources,
  project_total_funding
FROM project_repos
JOIN funded_projects USING project_id