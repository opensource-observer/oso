MODEL (
  name oso.stg_defillama__lp_fee_events,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  time::TIMESTAMP AS time,
  slug::VARCHAR AS slug,
  protocol::VARCHAR AS protocol,
  parent_protocol::VARCHAR AS parent_protocol,
  chain::VARCHAR AS chain,
  token::VARCHAR AS token,
  fees_usd::DOUBLE AS fees_usd
FROM @oso_source('bigquery.defillama.lp_fee_events')
