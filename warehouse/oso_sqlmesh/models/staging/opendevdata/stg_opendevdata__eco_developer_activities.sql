MODEL (
  name oso.stg_opendevdata__eco_developer_activities,
  description 'Staging model for opendevdata eco_developer_activities',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  ecosystem_id::BIGINT AS ecosystem_id,
  day::DATE AS day,
  canonical_developer_id::BIGINT AS canonical_developer_id,
  CAST(repo_ids AS ROW(list ARRAY(ROW(element BIGINT)))) AS repo_ids,
  num_commits::BIGINT AS num_commits,
  is_exclusive::BOOLEAN AS is_exclusive
FROM @oso_source('bigquery.opendevdata.eco_developer_activities')
