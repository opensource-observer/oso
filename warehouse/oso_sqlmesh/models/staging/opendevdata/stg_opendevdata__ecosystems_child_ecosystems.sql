MODEL (
  name oso.stg_opendevdata__ecosystems_child_ecosystems,
  description 'Staging model for opendevdata ecosystems_child_ecosystems',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  created_at::TIMESTAMP AS created_at,
  parent_id::BIGINT AS parent_id,
  child_id::BIGINT AS child_id,
  connected_at::TIMESTAMP AS connected_at
FROM @oso_source('bigquery.opendevdata.ecosystems_child_ecosystems')
