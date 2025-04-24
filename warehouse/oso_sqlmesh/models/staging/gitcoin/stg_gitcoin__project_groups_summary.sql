MODEL (
  name oso.stg_gitcoin__project_groups_summary,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column latest_project_application_timestamp,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  grain (latest_project_application_timestamp, gitcoin_group_id, latest_gitcoin_project_id)
);

SELECT
  DATE_TRUNC('DAY', latest_created_application::DATE) AS latest_project_application_timestamp,
  group_id::VARCHAR AS gitcoin_group_id,
  latest_created_project_id::VARCHAR AS latest_gitcoin_project_id,
  total_amount_donated::FLOAT AS total_amount_donated_in_usd,
  application_count::INTEGER AS group_application_count,
  latest_source::VARCHAR AS latest_gitcoin_data_source,
  trim(title)::VARCHAR AS project_application_title,
  lower(latest_payout_address)::VARCHAR AS latest_project_recipient_address,
  trim(lower(latest_website))::VARCHAR AS latest_project_website,
  trim(lower(latest_project_twitter))::VARCHAR AS latest_project_twitter,
  trim(lower(latest_project_github))::VARCHAR AS latest_project_github
FROM @oso_source('bigquery.gitcoin.project_groups_summary')
WHERE latest_created_application BETWEEN @start_dt AND @end_dt