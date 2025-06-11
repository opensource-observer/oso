MODEL (
  name oso.stg_chainlist__chains,
  description 'The most recent view of chains and their RPC endpoints from the chainlist dagster source',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  name::VARCHAR AS name,
  chain::VARCHAR AS chain,
  chain_id::INTEGER AS chain_id,
  network_id::INTEGER AS network_id,
  short_name::VARCHAR AS short_name,
  chain_slug::VARCHAR AS chain_slug,
  native_currency_name::VARCHAR AS native_currency_name,
  native_currency_symbol::VARCHAR AS native_currency_symbol,
  native_currency_decimals::INTEGER AS native_currency_decimals,
  info_url::VARCHAR AS info_url
FROM @oso_source('bigquery.chainlist.chains') AS chains
