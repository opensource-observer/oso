MODEL (
  name oso.stg_growthepie__fundamentals_full,
  description 'Fundamental metrics for different chains from growthepie',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  metric_key::VARCHAR AS metric_key,
  UPPER(origin_key::VARCHAR) AS origin_key,
  date::DATE AS date,
  value::DOUBLE AS value
FROM @oso_source('bigquery.growthepie.fundamentals_full') 