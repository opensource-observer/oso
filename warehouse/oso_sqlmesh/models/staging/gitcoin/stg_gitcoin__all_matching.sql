MODEL (
  name oso.stg_gitcoin__all_matching,
  description "Staging table for Gitcoin matching data",
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  timestamp::TIMESTAMP AS timestamp,
  LOWER(round_id)::VARCHAR AS round_id,
  round_num::INTEGER AS round_number,
  chain_id::INTEGER AS chain_id,
  LOWER(project_id)::VARCHAR AS project_id,
  TRIM(title)::VARCHAR AS title,
  LOWER(recipient_address)::VARCHAR AS recipient_address,
  match_amount_in_usd::DOUBLE AS match_amount_in_usd
FROM @oso_source('bigquery.gitcoin.all_matching')