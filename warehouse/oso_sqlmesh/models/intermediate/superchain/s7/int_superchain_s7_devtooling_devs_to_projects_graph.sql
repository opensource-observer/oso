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
   - For Builder Projects: ALL interactions from qualified developers are included
   - For Devtooling Projects: ALL interactions from qualified developers are included,
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

/* Identifies repositories that are either builder or devtooling projects */
WITH relevant_repos AS (
  SELECT DISTINCT 
    repo_artifact_id,
    repo_artifact_namespace,
    'builder' AS repo_type
  FROM oso.int_superchain_s7_devtooling_onchain_builder_nodes
  UNION
  SELECT DISTINCT 
    repo_artifact_id,
    repo_artifact_namespace,
    'devtooling' AS repo_type
  FROM oso.int_superchain_s7_devtooling_repositories
),

/* Collects all GitHub events for relevant repositories with developer and project mapping */
dev_events AS (
  SELECT    
    events.project_id,
    events.from_artifact_id AS developer_id,
    events.to_artifact_id AS repo_artifact_id,
    events.bucket_month,
    events.event_type,
    repos.repo_type,
    repos.repo_artifact_namespace
  FROM oso.int_events_monthly_to_project AS events
  JOIN relevant_repos AS repos
    ON events.to_artifact_id = repos.repo_artifact_id
  WHERE events.event_source = 'GITHUB'
),

/* Identifies developers who have committed code to builder projects */
onchain_developers AS (
  SELECT DISTINCT 
    developer_id,
    project_id
  FROM dev_events
  JOIN relevant_repos AS repos
    ON dev_events.repo_artifact_id = repos.repo_artifact_id
  WHERE
    event_type = 'COMMIT_CODE'
    AND repos.repo_type = 'builder'
    AND bucket_month >= @active_developer_date_threshold
),

/* Create a deduplicated mapping of projects to their types
   This explicitly identifies projects that are both builder and devtooling */
project_classification AS (
  SELECT
    project_id,
    BOOL_OR(repo_type = 'builder') AS is_builder_project,
    BOOL_OR(repo_type = 'devtooling') AS is_devtooling_project
  FROM dev_events
  GROUP BY project_id
),

/* Final selection: Gets all interactions where:
   1. Developer has committed to any builder project since 2024-01-01 (onchain_developers)
   AND
   2. The interaction is either:
      a) With a builder project (counted as builder interaction)
      b) With a devtooling project (counted as devtool interaction, unless the specific repo
         is also a builder repo - in that case it's already counted as a builder interaction) */

final_selection AS (
  SELECT
    dev_events.bucket_month,
    dev_events.project_id,
    dev_events.developer_id,
    LOWER(users.github_username) AS developer_name,
    dev_events.event_type,
    dev_events.repo_artifact_namespace
FROM dev_events
JOIN oso.int_github_users AS users
  ON dev_events.developer_id = users.user_id
WHERE dev_events.developer_id IN (SELECT developer_id FROM onchain_developers)
  AND (
    /* Include all builder interactions */
    dev_events.repo_type = 'builder'
    OR 
    /* Include devtooling interactions only if this project isn't also classified as a builder project */
    (dev_events.repo_type = 'devtooling'
     AND NOT EXISTS (
       SELECT 1
       FROM project_classification
       WHERE project_classification.project_id = dev_events.project_id
       AND project_classification.is_builder_project = TRUE
     ))
  )
  AND dev_events.event_type IN (
    'FORKED',
    'STARRED',
    'COMMIT_CODE',
    'ISSUE_COMMENT',
    'ISSUE_OPENED',
    'PULL_REQUEST_OPENED',
    'PULL_REQUEST_REVIEW_COMMENT'
  )
  AND NOT users.is_bot
)

SELECT DISTINCT
  bucket_month,
  project_id,
  developer_id,
  developer_name,
  event_type
FROM final_selection
WHERE repo_artifact_namespace != developer_name
