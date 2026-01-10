MODEL (
  name oso.stg_opendevdata__canonical_developers,
  description 'Staging model for opendevdata canonical_developers',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  primary_developer_email_identity_id::BIGINT AS primary_developer_email_identity_id,
  primary_github_user_id::VARCHAR AS primary_github_user_id
FROM @oso_source('bigquery.opendevdata.canonical_developers')
