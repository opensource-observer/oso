MODEL (
  name oso.stg_defillama__chains,
  description 'Chain data from DefiLlama API',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  gecko_id::VARCHAR AS gecko_id,
  tvl::DOUBLE AS tvl,
  token_symbol::VARCHAR AS token_symbol,
  cmc_id::VARCHAR AS cmc_id,
  name::VARCHAR AS name,
  chain_id::BIGINT AS chain_id
FROM @oso_source('bigquery.defillama.chains') 