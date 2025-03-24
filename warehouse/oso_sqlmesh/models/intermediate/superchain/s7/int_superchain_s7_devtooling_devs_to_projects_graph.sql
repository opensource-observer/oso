/*
This model creates a graph of interactions between developers and projects (both builder and devtooling).

Key concepts:
1. Qualified Developers: Developers who have committed code to any builder project since 2024-01-01
2. Project Types:
   - Builder projects: Projects identified in int_superchain_s7_devtooling_onchain_builder_nodes
   - Devtooling projects: Projects identified in int_superchain_s7_devtooling_repositories
   - Some projects may appear in both categories

Graph Construction Rules:
1. NODES:
   - Developers: Only includes qualified developers (must have committed to a builder project)
   - Projects: Includes both builder and devtooling projects
2. EDGES (interactions):
   - For Builder Projects: Only commits from qualified developers are included
   - For Devtooling Projects: ALL github events from qualified developers are included,
     UNLESS the project is also classified as a builder project (to avoid double-counting)
3. Edge Types (event_type):
   - FORKED
   - STARRED
   - COMMIT_CODE
   - ISSUE_COMMENT
   - ISSUE_OPENED
   - PULL_REQUEST_OPENED
   - PULL_REQUEST_REVIEW_COMMENT

Example:
- If Project A is only a devtool → Include all interactions from qualified developers
- If Project B is only a builder → Include all interactions from qualified developers
- If Project C is both a devtool and builder → Include interactions only on the builder side
*/

MODEL (
  name oso.int_superchain_s7_devtooling_devs_to_projects_graph,
  description 'Maps relationships between trusted developers, onchain builder projects, and devtooling projects',
  dialect trino,
  kind full,
  grain (bucket_month, developer_id, project_id, event_type),
);

@DEF(active_developer_date_threshold, DATE('2024-01-01'));
@DEF(trusted_developer_min_months, 3);

WITH commits_to_builder_projects AS (
  SELECT DISTINCT
    events.bucket_month,
    events.project_id,
    events.from_artifact_id AS developer_id,
    events.to_artifact_id AS repo_artifact_id,
    builder_repos.repo_artifact_namespace,
    events.event_type,
    'BUILDER' AS repo_type
  FROM oso.int_events_monthly_to_project AS events
  JOIN oso.int_superchain_s7_devtooling_onchain_builder_nodes AS builder_repos
    ON events.to_artifact_id = builder_repos.repo_artifact_id
  WHERE
    event_type = 'COMMIT_CODE'
    AND events.bucket_month >= @active_developer_date_threshold
),

trusted_developers AS (
  SELECT DISTINCT 
    events.developer_id,
    events.project_id,
    LOWER(users.github_username) AS developer_name,
    COUNT(DISTINCT events.bucket_month) AS months_active
  FROM commits_to_builder_projects AS events
  JOIN oso.int_github_users AS users
    ON events.developer_id = users.user_id
  WHERE users.is_bot = FALSE
  GROUP BY 1,2,3
  HAVING COUNT(DISTINCT events.bucket_month) >= @trusted_developer_min_months
),

github_events_to_devtooling_repos AS (
  SELECT DISTINCT
    events.bucket_month,
    events.project_id,
    events.from_artifact_id AS developer_id,
    events.to_artifact_id AS repo_artifact_id,
    devtool_repos.repo_artifact_namespace,
    events.event_type,
    'DEVTOOL' AS repo_type
  FROM oso.int_events_monthly_to_project AS events
  JOIN oso.int_superchain_s7_devtooling_repositories AS devtool_repos
    ON events.to_artifact_id = devtool_repos.repo_artifact_id
  WHERE events.event_source = 'GITHUB'
),

combined_events AS (
  SELECT * FROM commits_to_builder_projects
  UNION
  SELECT * FROM github_events_to_devtooling_repos
),

filtered_events AS (
  SELECT
    combined_events.bucket_month,
    combined_events.project_id,
    combined_events.developer_id,
    td.developer_name,
    combined_events.event_type,
    combined_events.repo_type,
    combined_events.repo_artifact_namespace
  FROM combined_events
  JOIN trusted_developers AS td
    ON combined_events.developer_id = td.developer_id
  WHERE event_type IN (
    'FORKED',
    'STARRED',
    'COMMIT_CODE',
    'ISSUE_COMMENT',
    'ISSUE_OPENED',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REVIEW_COMMENT'
  )
),

tagged_events AS (
  SELECT
    fe.bucket_month,
    fe.project_id,
    fe.developer_id,
    fe.developer_name,
    fe.event_type,
    fe.repo_artifact_namespace,
    CASE WHEN td.months_active IS NOT NULL THEN 'BUILDER' ELSE 'DEVTOOL' END
      AS relationship_type
  FROM filtered_events AS fe
  LEFT JOIN trusted_developers AS td
    ON fe.developer_id = td.developer_id
    AND fe.project_id = td.project_id
)

SELECT DISTINCT
  bucket_month,
  project_id,
  developer_id,
  developer_name,
  event_type,
  repo_artifact_namespace,
  relationship_type
FROM tagged_events
WHERE
  repo_artifact_namespace != developer_name
  AND NOT (relationship_type = 'BUILDER' AND event_type != 'COMMIT_CODE')
  