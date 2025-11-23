MODEL (
  name oso.stg_opendevdata__organizations,
  description 'Staging model for opendevdata organizations',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  created_at::TIMESTAMP AS created_at,
  name::VARCHAR AS name,
  link::VARCHAR AS link,
  github_created_at::TIMESTAMP AS github_created_at
FROM @oso_source('bigquery.opendevdata.organizations')
