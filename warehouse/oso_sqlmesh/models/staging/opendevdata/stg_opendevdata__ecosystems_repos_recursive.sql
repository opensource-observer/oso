MODEL (
  name oso.stg_opendevdata__ecosystems_repos_recursive,
  description 'Staging model for opendevdata ecosystems_repos_recursive',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  ecosystem_id::BIGINT AS ecosystem_id,
  repo_id::BIGINT AS repo_id,
  created_at::TIMESTAMP AS created_at,
  connected_at::DATE AS connected_at,
  CAST(path AS ROW(list ARRAY(ROW(element BIGINT)))) AS path,
  distance::BIGINT AS distance,
  is_explicit::BOOLEAN AS is_explicit,
  is_direct_exclusive::BOOLEAN AS is_direct_exclusive,
  is_indirect_exclusive::BOOLEAN AS is_indirect_exclusive,
  exclusive_at_connection::BOOLEAN AS exclusive_at_connection,
  exclusive_till::DATE AS exclusive_till
FROM @oso_source('bigquery.opendevdata.ecosystems_repos_recursive')
