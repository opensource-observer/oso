MODEL (
  name oso.stg_opendevdata__repo_developer_28d_activities,
  description 'Staging model for opendevdata repo_developer_28d_activities',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  repo_id::BIGINT AS repo_id,
  canonical_developer_id::BIGINT AS canonical_developer_id,
  day::DATE AS day,
  num_commits::BIGINT AS num_commits,
  original_day::DATE AS original_day,
  l28_days::BIGINT AS l28_days
FROM @oso_source('bigquery.opendevdata.repo_developer_28d_activities')
