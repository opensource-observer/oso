MODEL (
  name oso.stg_opendevdata__ecosystems_repos,
  description 'Staging model for opendevdata ecosystems_repos',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  created_at::TIMESTAMP AS created_at,
  ecosystem_id::BIGINT AS ecosystem_id,
  repo_id::BIGINT AS repo_id,
  connected_at::TIMESTAMP AS connected_at
FROM @oso_source('bigquery.opendevdata.ecosystems_repos')
