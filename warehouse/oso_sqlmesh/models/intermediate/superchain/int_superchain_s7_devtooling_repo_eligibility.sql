MODEL (
  name oso.int_superchain_s7_devtooling_repo_eligibility,
  description "Determines if a repository is eligible for measurement in the S7 devtooling round",
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id, repo_artifact_id)
);

@DEF(lookback_days, 180);

SELECT
  project_id,
  artifact_id AS repo_artifact_id,
  last_release_published,
  num_packages_in_deps_dev,
  num_dependent_repos_in_oso,
  is_fork,
  created_at,
  updated_at,
  CASE
    WHEN (
      CURRENT_TIMESTAMP + INTERVAL @lookback_days DAY >= last_release_published
      OR num_packages_in_deps_dev > 0
      OR num_dependent_repos_in_oso > 0
    )
    THEN TRUE
    ELSE FALSE
  END AS is_eligible,
  CURRENT_TIMESTAMP AS sample_date
FROM oso.int_repositories_enriched