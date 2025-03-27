MODEL (
  name oso.stg_defillama__tvl_events,
  kind FULL
);

SELECT
  time::TIMESTAMP AS time,
  slug::VARCHAR AS slug,
  protocol::VARCHAR AS protocol,
  parent_protocol::VARCHAR AS parent_protocol,
  chain::VARCHAR AS chain,
  token::VARCHAR AS token,
  tvl::DOUBLE AS tvl,
FROM @oso_source('bigquery.defillama.tvl_events')