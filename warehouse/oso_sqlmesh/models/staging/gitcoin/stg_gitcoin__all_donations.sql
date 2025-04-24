MODEL (
  name oso.stg_gitcoin__all_donations,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by ("round_id"),
  grain (bucket_day, donor_address, project_recipient_address, gitcoin_project_id, gitcoin_round_id, chain_id)
);

SELECT
  source::VARCHAR AS gitcoin_data_source,
  DATE_TRUNC('DAY', timestamp::DATE) AS bucket_day,
  round_id::VARCHAR AS gitcoin_round_id,
  round_num::INTEGER AS round_number,  
  round_name::VARCHAR AS round_name,
  chain_id::INTEGER AS chain_id,
  project_id::VARCHAR AS gitcoin_project_id,
  trim(project_name)::VARCHAR AS project_application_title,
  lower(recipient_address)::VARCHAR AS project_recipient_address,
  lower(donor_address)::VARCHAR AS donor_address,
  lower(transaction_hash)::VARCHAR AS transaction_hash,
  amount_in_usd::FLOAT AS amount_in_usd,
FROM @oso_source('bigquery.gitcoin.all_donations')
WHERE time BETWEEN @start_dt AND @end_dt