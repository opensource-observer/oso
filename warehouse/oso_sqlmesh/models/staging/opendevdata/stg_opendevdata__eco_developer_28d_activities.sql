MODEL (
  name oso.stg_opendevdata__eco_developer_28d_activities,
  description 'Staging model for opendevdata eco_developer_28d_activities',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  ecosystem_id::BIGINT AS ecosystem_id,
  canonical_developer_id::BIGINT AS canonical_developer_id,
  day::DATE AS day,
  CAST(repo_ids AS ROW(list ARRAY(ROW(element BIGINT)))) AS repo_ids,
  num_commits::BIGINT AS num_commits,
  original_day::DATE AS original_day,
  is_exclusive_28d::BOOLEAN AS is_exclusive_28d,
  l28_days::BIGINT AS l28_days
FROM @oso_source('bigquery.opendevdata.eco_developer_28d_activities')
