MODEL (
  name oso.stg_defillama__trading_volume_events,
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
  event_type::VARCHAR AS event_type,
  amount::DOUBLE AS amount
FROM @oso_source('bigquery.defillama.trading_volume_events')