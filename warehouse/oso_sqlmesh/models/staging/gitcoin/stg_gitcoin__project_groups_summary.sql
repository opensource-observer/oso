MODEL (
  name oso.stg_gitcoin__project_groups_summary,
  description "Staging table for data on Gitcoin project groups",
  kind full,
  cron '@daily',
  dialect trino,
  grain (latest_project_application_timestamp, gitcoin_group_id, latest_gitcoin_project_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  CONCAT('GITCOIN_', UPPER(latest_source))::VARCHAR AS source,
  latest_created_application::TIMESTAMP AS updated_at,
  LOWER(group_id)::VARCHAR AS group_id,
  LOWER(latest_created_project_id)::VARCHAR AS project_id,
  total_amount_donated::FLOAT AS total_amount_donated_in_usd,
  application_count::INTEGER AS group_application_count,
  TRIM(title)::VARCHAR AS project_application_title,
  TRIM(LOWER(latest_payout_address))::VARCHAR AS payout_address,
  TRIM(LOWER(latest_website))::VARCHAR AS website,
  TRIM(LOWER(latest_project_twitter))::VARCHAR AS twitter,
  TRIM(LOWER(latest_project_github))::VARCHAR AS github
FROM @oso_source('bigquery.gitcoin.project_groups_summary')