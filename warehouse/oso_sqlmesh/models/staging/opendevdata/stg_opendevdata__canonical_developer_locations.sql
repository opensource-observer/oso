MODEL (
  name oso.stg_opendevdata__canonical_developer_locations,
  description 'Staging model for opendevdata canonical_developer_locations',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  canonical_developer_id::BIGINT AS canonical_developer_id,
  created_at::TIMESTAMP AS created_at,
  input::VARCHAR AS input,
  country::VARCHAR AS country,
  admin_level_1::VARCHAR AS admin_level_1,
  admin_level_2::VARCHAR AS admin_level_2,
  locality::VARCHAR AS locality,
  sublocality::VARCHAR AS sublocality,
  formatted_address::VARCHAR AS formatted_address,
  lat::DOUBLE AS lat,
  lng::DOUBLE AS lng,
  raw::VARCHAR AS raw
FROM @oso_source('bigquery.opendevdata.canonical_developer_locations')
