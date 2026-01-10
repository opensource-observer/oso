MODEL (
  name oso.stg_opendevdata__eco_developer_contribution_ranks,
  description 'Staging model for opendevdata eco_developer_contribution_ranks',
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
  points::BIGINT AS points,
  points_28d::BIGINT AS points_28d,
  points_56d::BIGINT AS points_56d,
  contribution_rank::VARCHAR AS contribution_rank
FROM @oso_source('bigquery.opendevdata.eco_developer_contribution_ranks')
