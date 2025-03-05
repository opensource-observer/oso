MODEL (
  name oso.int_superchain_s7_trusted_developers,
  description "Identifies trusted developers based on commit history to relevant onchain builder repositories",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id, developer_id)
);

@DEF(min_repo_stars, 5);

@DEF(last_repo_update_date, '2024-07-01');

@DEF(active_months_threshold, 3);

@DEF(commits_threshold, 20);

@DEF(last_commit_threshold_months, 12);

WITH eligible_onchain_builder_repos AS (
  SELECT
    repos.artifact_id AS repo_artifact_id,
    repos.project_id,
    builders.sample_date::TIMESTAMP AS sample_date
  FROM oso.int_repositories_enriched AS repos
  INNER JOIN oso.int_superchain_s7_onchain_builder_eligibility AS builders
    ON repos.project_id = builders.project_id
  WHERE
    repos.language IN ('TypeScript', 'Solidity', 'Rust')
    AND repos.updated_at > @last_repo_update_date::TIMESTAMP
    AND repos.star_count > @min_repo_stars
    AND builders.is_eligible
    AND builders.sample_date BETWEEN @start_dt AND @end_dt
), developer_activity AS (
  SELECT
    repos.project_id,
    repos.sample_date,
    events.developer_id,
    events.developer_name,
    SUM(events.total_events) AS total_commits_to_project,
    MIN(events.first_event) AS first_commit,
    MAX(events.last_event) AS last_commit
  FROM oso.int_developer_activity_by_repo AS events
  INNER JOIN eligible_onchain_builder_repos AS repos
    ON events.repo_artifact_id = repos.repo_artifact_id
  WHERE
    events.event_type = 'COMMIT_CODE'
  GROUP BY
    repos.project_id,
    repos.sample_date,
    events.developer_id,
    events.developer_name
), eligible_developers AS (
  SELECT DISTINCT
    developer_id
  FROM developer_activity
  WHERE
    total_commits_to_project >= @commits_threshold
    AND DATEDIFF('month', CAST(first_commit AS TIMESTAMP), CAST(last_commit AS TIMESTAMP)) >= @active_months_threshold
    AND CAST(last_commit AS DATE) >= CURRENT_DATE - INTERVAL @last_commit_threshold_months MONTH
)
SELECT
  sample_date,
  project_id,
  developer_id,
  developer_name,
  total_commits_to_project,
  first_commit,
  last_commit
FROM developer_activity
WHERE
  developer_id IN (
    SELECT
      developer_id
    FROM eligible_developers
  )