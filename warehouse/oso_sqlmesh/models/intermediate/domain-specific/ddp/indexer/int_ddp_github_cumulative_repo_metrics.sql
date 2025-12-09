MODEL (
  name oso.int_ddp_github_cumulative_repo_metrics,
  description 'Cumulative GitHub Events by Repository from GitHub Archive since 2025-01-01',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  tags (
    "github",
    "ddp",
  ),
);

WITH current_repo AS (
  SELECT
    repo_id,
    MAX_BY(repo_name, last_event_date) AS repo_name,
    SUM(total_events) AS total_events,
    MIN(CASE WHEN event_type = 'COMMIT_CODE' THEN first_event_date END) AS first_code_contribution_date,
    MAX(CASE WHEN event_type = 'COMMIT_CODE' THEN last_event_date END) AS last_code_contribution_date
  FROM oso.int_ddp_github_repo_user_summary_metrics
  GROUP BY repo_id
),
actor_activities AS (
  -- Aggregate actor activities across event types per repo
  SELECT
    s.repo_id,
    s.actor_id,
    MAX(CASE WHEN s.is_maintainer = TRUE THEN 1 ELSE 0 END) AS is_maintainer,
    MAX(CASE WHEN s.event_type = 'COMMIT_CODE' THEN 1 ELSE 0 END) AS has_commit_code,
    MAX(CASE WHEN s.event_type = 'OTHER' THEN 1 ELSE 0 END) AS has_other,
    MAX(CASE WHEN s.event_type = 'STARRED' THEN 1 ELSE 0 END) AS has_starred,
    MAX(CASE WHEN s.is_maintainer = TRUE AND s.event_type = 'COMMIT_CODE' THEN 1 ELSE 0 END) AS is_maintainer_committer
  FROM oso.int_ddp_github_repo_user_summary_metrics AS s
  GROUP BY 1,2
),
contributor_categories AS (
  -- Categorize contributors with priority
  SELECT
    repo_id,
    actor_id,
    CASE
      WHEN is_maintainer = 1 THEN 'PERSONAL_MAINTAINER'
      WHEN has_commit_code = 1 THEN 'CODE_CONTRIBUTOR'
      WHEN has_other = 1 THEN 'OTHER_CONTRIBUTOR'
      WHEN has_starred = 1 THEN 'STARGAZER'
      ELSE 'UNKNOWN'
    END AS contributor_category,
    is_maintainer_committer
  FROM actor_activities
),
contributor_counts AS (
  -- Aggregate contributor counts per repo
  SELECT
    repo_id,
    COUNT(DISTINCT CASE WHEN contributor_category = 'CODE_CONTRIBUTOR' THEN actor_id END) AS code_contributor_count,
    COUNT(DISTINCT CASE WHEN contributor_category = 'OTHER_CONTRIBUTOR' THEN actor_id END) AS other_contributor_count,
    COUNT(DISTINCT CASE WHEN contributor_category = 'STARGAZER' THEN actor_id END) AS stargazer_count,
    COUNT(DISTINCT CASE WHEN contributor_category = 'PERSONAL_MAINTAINER' THEN actor_id END) AS personal_maintainer_count,
    COUNT(DISTINCT CASE WHEN is_maintainer_committer = 1 THEN actor_id END) AS maintainer_code_contributor_count
  FROM contributor_categories
  GROUP BY 1
),
repo_aggregates AS (
  -- Combine all metrics
  SELECT
    cr.repo_id,
    cr.repo_name,
    SPLIT_PART(cr.repo_name, '/', 1) AS repo_maintainer,
    cc.code_contributor_count,
    cc.other_contributor_count,
    cc.stargazer_count,
    cc.personal_maintainer_count,
    cc.maintainer_code_contributor_count,
    cr.total_events,
    cr.first_code_contribution_date,
    cr.last_code_contribution_date
  FROM current_repo AS cr
  INNER JOIN contributor_counts AS cc
    ON cr.repo_id = cc.repo_id
)
SELECT
  repo_id,
  repo_name,
  repo_maintainer,
  code_contributor_count,
  other_contributor_count,
  stargazer_count,
  personal_maintainer_count,
  maintainer_code_contributor_count,
  total_events,
  first_code_contribution_date,
  last_code_contribution_date
FROM repo_aggregates