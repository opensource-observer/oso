MODEL (
  name oso.stg_defillama__protocol_metadata,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::VARCHAR AS id,
  LOWER(slug::VARCHAR) AS slug,
  name::VARCHAR AS name,
  LOWER(address::VARCHAR) AS address,
  symbol::VARCHAR AS symbol,
  url::VARCHAR AS url,
  description::VARCHAR AS description,
  logo::VARCHAR AS logo,
  chain::VARCHAR AS chain,
  category::VARCHAR AS category,
  LOWER(twitter::VARCHAR) AS twitter,
  LOWER(parent_protocol::VARCHAR) AS parent_protocol
FROM @oso_source('bigquery.defillama.protocol_metadata')
