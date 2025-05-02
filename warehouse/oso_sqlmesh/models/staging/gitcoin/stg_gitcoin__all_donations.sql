MODEL (
  name oso.stg_gitcoin__all_donations,
  description "Staging table for Gitcoin donations data",
  kind full,
  cron '@monthly',
  dialect trino,
  grain (time, project_recipient_address, gitcoin_project_id, gitcoin_round_id, chain_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  timestamp::TIMESTAMP AS timestamp,
  LOWER(round_id)::VARCHAR AS round_id,
  round_num::INTEGER AS round_number,  
  round_name::VARCHAR AS round_name,
  chain_id::INTEGER AS chain_id,
  LOWER(project_id)::VARCHAR AS project_id,
  TRIM(project_name)::VARCHAR AS project_name,
  LOWER(recipient_address)::VARCHAR AS recipient_address,
  LOWER(donor_address)::VARCHAR AS donor_address,
  LOWER(transaction_hash)::VARCHAR AS transaction_hash,
  amount_in_usd::DOUBLE AS amount_in_usd
FROM @oso_source('bigquery.gitcoin.all_donations')
WHERE amount_in_usd > 0