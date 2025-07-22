MODEL (
  name oso.stg_defillama__historical_chain_tvl,
  description 'Historical TVL values for individual chains from DefiLlama',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  time::TIMESTAMP AS time,
  LOWER(chain::VARCHAR) AS chain,
  tvl::DOUBLE AS tvl
FROM @oso_source('bigquery.defillama.historical_chain_tvl') 