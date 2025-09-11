MODEL (
  name oso.stg_l2beat__tvs,
  description 'L2beat Total Value Secured (TVS) data for various blockchain projects',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  project_slug::VARCHAR AS project_slug,
  @from_unix_timestamp(timestamp) AS timestamp,
  native::BIGINT AS native,
  canonical::BIGINT AS canonical,
  external::BIGINT AS external,
  eth_price::DOUBLE AS eth_price,
  canonical__v_double::DOUBLE AS canonical__v_double,
  external__v_double::DOUBLE AS external__v_double,
  native__v_double::DOUBLE AS native__v_double
FROM @oso_source('bigquery.l2beat.tvs')
