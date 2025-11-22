MODEL (
  name oso.stg_opendevdata__ecosystems_child_ecosystems_recursive,
  description 'Staging model for opendevdata ecosystems_child_ecosystems_recursive',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  parent_id::BIGINT AS parent_id,
  child_id::BIGINT AS child_id,
  created_at::TIMESTAMP AS created_at,
  ecosystem_ecosystem_paths::TEXT AS ecosystem_ecosystem_paths,
  ecosystem_chain_ecosystem_paths::TEXT AS ecosystem_chain_ecosystem_paths,
  connection_dates::TEXT AS connection_dates,
  connected_at::DATE AS connected_at
FROM @oso_source('bigquery.opendevdata.ecosystems_child_ecosystems_recursive')
