MODEL (
  name oso.stg_opendevdata__ecosystems_organizations,
  description 'Staging model for opendevdata ecosystems_organizations',
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
  organization_id::BIGINT AS organization_id,
  is_first_party::BIGINT AS is_first_party
FROM @oso_source('bigquery.opendevdata.ecosystems_organizations')
