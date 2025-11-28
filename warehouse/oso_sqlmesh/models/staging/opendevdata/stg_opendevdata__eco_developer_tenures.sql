MODEL (
  name oso.stg_opendevdata__eco_developer_tenures,
  description 'Staging model for opendevdata eco_developer_tenures',
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
  tenure_days::BIGINT AS tenure_days,
  category::BIGINT AS category
FROM @oso_source('bigquery.opendevdata.eco_developer_tenures')
