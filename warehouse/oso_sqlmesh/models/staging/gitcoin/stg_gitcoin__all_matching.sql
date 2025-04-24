MODEL (
  name oso.stg_gitcoin__all_matching,
  description "Staging table for Gitcoin matching data",
  kind full,
  cron '@daily',
  dialect trino,
  grain (time, project_recipient_address, gitcoin_project_id, gitcoin_round_id, chain_id)
);

SELECT distinct
  'MatchFunding' as gitcoin_data_source,
  timestamp::DATE AS time,
  round_id::VARCHAR AS gitcoin_round_id,
  round_num::INTEGER AS round_number,
  round_name::VARCHAR as round_name,
  chain_id::INTEGER AS chain_id,
  project_id::VARCHAR AS gitcoin_project_id,
  trim(title)::VARCHAR AS project_application_title,
  lower(recipient_address)::VARCHAR AS project_recipient_address,
  match_amount_in_usd::DOUBLE AS amount_in_usd
FROM @oso_source('bigquery.gitcoin.all_matching')
WHERE match_amount_in_usd > 0