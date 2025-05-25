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
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

@DEF(active_developer_date_threshold, DATE('2024-01-01'));
@DEF(trusted_developer_min_months, 3);


WITH
-- 1) builder <> repo <> project
builder_repos AS (
  SELECT
    repo_artifact_id,
    repo_artifact_namespace,
    project_id AS builder_project_id
  FROM oso.int_superchain_s7_devtooling_onchain_builder_nodes
),
-- 2) devtool <> repo <> project
devtool_repos AS (
  SELECT
    repo_artifact_id,
    repo_artifact_namespace,
    project_id AS devtool_project_id
  FROM oso.int_superchain_s7_devtooling_repositories
),
-- 3) link devtool projects back to related builder projects (via shared repo)
related_projects AS (
  SELECT DISTINCT
    dr.devtool_project_id,
    br.builder_project_id
  FROM devtool_repos AS dr
  JOIN builder_repos AS br
    ON dr.repo_artifact_id = br.repo_artifact_id
),
-- 4) all the GitHub events we care about, excluding bots
filtered_events AS (
  SELECT
    DATE_TRUNC('MONTH', e.bucket_day) AS bucket_month,
    e.event_type,
    e.to_artifact_id AS repo_artifact_id,
    e.from_artifact_id AS developer_id,
    LOWER(u.github_username) AS developer_name
  FROM oso.int_events_daily__github AS e
  JOIN oso.int_github_users AS u
    ON e.from_artifact_id = u.user_id
  WHERE
    u.is_bot = FALSE
    AND e.event_type IN (
      'FORKED',
      'STARRED',
      'COMMIT_CODE',
      'ISSUE_COMMENT',
      'ISSUE_OPENED',
      'PULL_REQUEST_OPENED',
      'PULL_REQUEST_REVIEW_COMMENT'
    )
),
-- 5) restrict builder events by date and event type
builder_events AS (
  SELECT
    fe.bucket_month,
    fe.event_type,
    fe.developer_id,
    fe.developer_name,
    br.builder_project_id,
    br.repo_artifact_id,
    br.repo_artifact_namespace
  FROM filtered_events AS fe
  JOIN builder_repos AS br
    ON fe.repo_artifact_id = br.repo_artifact_id
  WHERE
    fe.event_type = 'COMMIT_CODE'
    AND fe.bucket_month >= @active_developer_date_threshold
),
-- 6) "trusted" if commit-code in >=3 distinct months
trusted_developers AS (
  SELECT developer_id
  FROM builder_events
  GROUP BY developer_id
  HAVING COUNT(DISTINCT bucket_month) >= @trusted_developer_min_months
),
-- 7) which builder projects each trusted dev has hit
developer_builder_projects AS (
  SELECT DISTINCT
    developer_id,
    builder_project_id
  FROM builder_events
),
-- 8) enrich devtool events with related builder project
devtool_events AS (
  SELECT
    fe.bucket_month,
    fe.event_type,
    fe.developer_id,
    fe.developer_name,
    dr.devtool_project_id,
    dr.repo_artifact_id,
    dr.repo_artifact_namespace,
    rp.builder_project_id AS related_builder_project_id
  FROM filtered_events AS fe
  JOIN devtool_repos AS dr
    ON fe.repo_artifact_id = dr.repo_artifact_id
  LEFT JOIN related_projects AS rp
    ON dr.devtool_project_id = rp.devtool_project_id
),
-- 9) builder‐side graph: only commits
builder_graph AS (
  SELECT
    be.bucket_month,
    be.event_type,
    be.developer_id,
    be.developer_name,
    be.repo_artifact_namespace,
    be.builder_project_id AS project_id,
    'BUILDER' AS relationship_type
  FROM builder_events AS be
  JOIN trusted_developers AS td
    ON be.developer_id = td.developer_id
),
-- 10) devtool-side graph: all events, but exclude
--    a) devtools under a builder they've already committed to
--    b) self-owned devtool repos
devtool_graph AS (
  SELECT
    de.bucket_month,
    de.event_type,
    de.developer_id,
    de.developer_name,
    de.repo_artifact_namespace,
    de.devtool_project_id AS project_id,
    'DEVTOOL' AS relationship_type
  FROM devtool_events AS de
  JOIN trusted_developers AS td
    ON de.developer_id = td.developer_id
  LEFT JOIN developer_builder_projects AS dbp
    ON de.developer_id = dbp.developer_id
   AND de.related_builder_project_id = dbp.builder_project_id
  WHERE
    (
      de.related_builder_project_id IS NULL -- devtool stands alone
      OR dbp.builder_project_id IS NULL  -- didn't commit to related builder
    )
    AND de.developer_name != de.repo_artifact_namespace  -- not their own repo
),
-- 11) final union
final_graph AS (
  SELECT * FROM builder_graph
  UNION ALL
  SELECT * FROM devtool_graph
)

SELECT DISTINCT
  bucket_month,
  event_type,
  developer_id,
  developer_name,
  repo_artifact_namespace,
  project_id,
  relationship_type
FROM final_graph