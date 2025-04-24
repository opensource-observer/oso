MODEL (
  name oso.stg_gitcoin__project_lookup,
  kind FULL,
  cron '@daily',
  grain (gitcoin_group_id, gitcoin_project_id)
);

SELECT
  group_id::VARCHAR AS gitcoin_group_id,
  project_id::VARCHAR AS gitcoin_project_id,
  source::VARCHAR AS latest_gitcoin_data_source
FROM @oso_source('bigquery.gitcoin.project_lookup')
