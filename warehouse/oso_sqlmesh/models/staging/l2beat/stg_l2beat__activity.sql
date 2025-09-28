MODEL (
  name oso.stg_l2beat__activity,
  description 'L2beat activity data for various blockchain projects',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  project_slug::VARCHAR AS project_slug,
  @from_unix_timestamp(timestamp) AS timestamp,
  count::BIGINT AS count,
  uops_count::BIGINT AS uops_count
FROM @oso_source('bigquery.l2beat.activity')
