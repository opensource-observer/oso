MODEL (
  name oso.int_superchain_s7_developers_to_projects_graph,
  description 'Maps relationships between trusted developers, onchain builder projects, and devtooling projects',
  kind full,
);

@DEF(active_developer_date_threshold, DATE('2024-01-01'));

WITH dev_events AS (
  SELECT    
    devs.developer_id,
    devs.developer_name,
    repos.project_id,
    repos.artifact_id AS repo_artifact_id,
    repos.language,
    repos.project_id,
    DATE_TRUNC('MONTH', events.time::DATE) AS bucket_month,
    events.event_type
  FROM oso.int_events_filtered__github AS events
  JOIN oso.int_repositories_enriched AS repos
    ON events.to_artifact_id = repos.artifact_id
  JOIN oso.int_developer_activity_by_repo AS devs
    ON events.from_artifact_id = devs.developer_id
),

builder_github_repos AS (
  SELECT DISTINCT repos.artifact_id AS repo_artifact_id
  FROM oso.int_repositories_enriched AS repos
  JOIN oso.int_superchain_s7_devtooling_onchain_builder_nodes AS nodes
    ON repos.project_id = nodes.project_id
  WHERE language IN ('TypeScript', 'Solidity', 'Rust', 'Vyper')
),

onchain_developers AS (
  SELECT DISTINCT developer_id
  FROM dev_events
  WHERE
    event_type = 'COMMIT_CODE'
    AND repo_artifact_id IN (SELECT repo_artifact_id FROM builder_github_repos)
    AND bucket_month >= @active_developer_date_threshold
),

relevant_projects AS (
  SELECT DISTINCT abp.project_id
  FROM oso.artifacts_by_project_v1 AS abp
  JOIN oso.projects_by_collection_v1 AS pbc
    ON abp.project_id = pbc.project_id
  WHERE 
    abp.artifact_source = 'GITHUB'
    AND (
      abp.artifact_id IN (SELECT repo_artifact_id FROM builder_github_repos)
      OR pbc.collection_name = '7-1'
    )
)

SELECT DISTINCT
  bucket_month,
  project_id,
  developer_id,
  developer_name,
  event_type
FROM dev_events
WHERE
  developer_id IN (SELECT developer_id FROM onchain_developers)
  AND project_id IN (SELECT project_id FROM relevant_projects)
  AND event_type IN (
    'FORKED',
    'STARRED',
    'COMMIT_CODE',
    'ISSUE_COMMENT',
    'ISSUE_OPENED',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REVIEW_COMMENT'
)