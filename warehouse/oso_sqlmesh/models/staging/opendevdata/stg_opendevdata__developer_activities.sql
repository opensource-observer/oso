MODEL (
  name oso.stg_opendevdata__developer_activities,
  description 'Staging model for opendevdata developer_activities',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  repo_id::BIGINT AS repo_id,
  day::DATE AS day,
  canonical_developer_id::BIGINT AS canonical_developer_id,
  num_commits::BIGINT AS num_commits
FROM @oso_source('bigquery.opendevdata.developer_activities')
