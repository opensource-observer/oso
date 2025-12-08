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
  )
);

WITH repo_maintainers AS (
  SELECT DISTINCT
    repo_id,
    repo_name,
    SPLIT_PART(repo_name, '/', 1) AS repo_maintainer
  FROM oso.int_ddp_github_events_daily
),
contributor_event_types AS (
  SELECT
    e.repo_id,
    e.repo_name,
    e.actor_id,
    CASE
      WHEN MAX(e.actor_login) = rm.repo_maintainer THEN 'PERSONAL_MAINTAINER'
      WHEN MAX(CASE WHEN e.event_type = 'COMMIT_CODE' THEN 1 ELSE 0 END) = 1 THEN 'CODE_CONTRIBUTOR'
      WHEN MAX(CASE WHEN e.event_type = 'OTHER' THEN 1 ELSE 0 END) = 1 THEN 'OTHER_CONTRIBUTOR'
      WHEN MAX(CASE WHEN e.event_type = 'STARRED' THEN 1 ELSE 0 END) = 1 THEN 'STARGAZER'
      ELSE 'UNKNOWN'
    END AS contributor_category
  FROM oso.int_ddp_github_events_daily AS e
  JOIN repo_maintainers AS rm
    ON e.repo_id = rm.repo_id
  GROUP BY e.repo_id, e.repo_name, e.actor_id, rm.repo_maintainer
),
maintainer_code_commits AS (
  SELECT
    e.repo_id,
    e.repo_name,
    COUNT(DISTINCT CASE 
      WHEN e.actor_login = rm.repo_maintainer 
        AND e.event_type = 'COMMIT_CODE' 
      THEN e.actor_id 
    END) AS maintainer_code_contributor_count
  FROM oso.int_ddp_github_events_daily AS e
  JOIN repo_maintainers AS rm
    ON e.repo_id = rm.repo_id
  GROUP BY e.repo_id, e.repo_name
),
aggregated_events AS (
  SELECT
    repo_id,
    repo_name,
    COUNT(DISTINCT bucket_day) AS total_days_with_activity,
    SUM(amount) AS total_events
  FROM oso.int_ddp_github_events_daily
  GROUP BY repo_id, repo_name
),
code_contribution_dates AS (
  SELECT
    repo_id,
    repo_name,
    MIN(bucket_day) AS first_code_contribution_date,
    MAX(bucket_day) AS last_code_contribution_date
  FROM oso.int_ddp_github_events_daily
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY repo_id, repo_name
),
contributor_counts AS (
  SELECT
    repo_id,
    repo_name,
    COUNT(DISTINCT CASE WHEN contributor_category = 'CODE_CONTRIBUTOR' THEN actor_id END)
      AS code_contributor_count,
    COUNT(DISTINCT CASE WHEN contributor_category = 'OTHER_CONTRIBUTOR' THEN actor_id END)
      AS other_contributor_count,
    COUNT(DISTINCT CASE WHEN contributor_category = 'STARGAZER' THEN actor_id END)
      AS stargazer_count,
    COUNT(DISTINCT CASE WHEN contributor_category = 'PERSONAL_MAINTAINER' THEN actor_id END)
      AS personal_maintainer_count
  FROM contributor_event_types
  GROUP BY repo_id, repo_name
)
SELECT
  cc.repo_id,
  cc.repo_name,
  rm.repo_maintainer,
  cc.code_contributor_count,
  cc.other_contributor_count,
  cc.stargazer_count,
  cc.personal_maintainer_count,
  COALESCE(mcc.maintainer_code_contributor_count, 0) AS maintainer_code_contributor_count,
  ae.total_events,
  ae.total_days_with_activity,
  ccd.first_code_contribution_date,
  ccd.last_code_contribution_date
FROM contributor_counts AS cc
JOIN repo_maintainers AS rm
  ON cc.repo_id = rm.repo_id
JOIN aggregated_events AS ae
  ON cc.repo_id = ae.repo_id
JOIN code_contribution_dates AS ccd
  ON cc.repo_id = ccd.repo_id
JOIN maintainer_code_commits AS mcc
  ON cc.repo_id = mcc.repo_id  