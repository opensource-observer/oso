MODEL (
  name oso.stg_crypto_ecosystems__taxonomy,
  description 'Staging model for crypto ecosystem taxonomy data from the crypto-ecosystems repository with unnested arrays',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


SELECT
  LOWER(repo_url::VARCHAR) AS repo_url,
  eco_name::VARCHAR AS eco_name,
  branch::ARRAY<VARCHAR> AS branch,
  tags::ARRAY<VARCHAR> AS tags
FROM @oso_source('bigquery.crypto_ecosystems.taxonomy')