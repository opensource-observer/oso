MODEL (
  name oso.stg_gitcoin__all_donations,
  description "Staging table for Gitcoin donations data",
  kind full,
  cron '@daily',
  dialect trino,
  grain (time, project_recipient_address, gitcoin_project_id, gitcoin_round_id, chain_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  source::VARCHAR AS gitcoin_data_source,
  timestamp::DATE AS time,
  round_id::VARCHAR AS gitcoin_round_id,
  round_num::INTEGER AS round_number,  
  round_name::VARCHAR AS round_name,
  chain_id::INTEGER AS chain_id,
  project_id::VARCHAR AS gitcoin_project_id,
  trim(project_name)::VARCHAR AS project_application_title,
  lower(recipient_address)::VARCHAR AS project_recipient_address,
  lower(donor_address)::VARCHAR AS donor_address,
  lower(transaction_hash)::VARCHAR AS transaction_hash,
  amount_in_usd::DOUBLE AS amount_in_usd
FROM @oso_source('bigquery.gitcoin.all_donations')
WHERE amount_in_usd > 0