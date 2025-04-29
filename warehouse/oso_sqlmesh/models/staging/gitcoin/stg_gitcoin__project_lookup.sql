MODEL (
  name oso.stg_gitcoin__project_lookup,
  description "Staging table mapping Gitcoin project group to projects",
  kind FULL,
  cron '@daily',
  dialect trino,
  grain (gitcoin_group_id, gitcoin_project_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  group_id::VARCHAR AS gitcoin_group_id,
  project_id::VARCHAR AS gitcoin_project_id,
  source::VARCHAR AS latest_gitcoin_data_source
FROM @oso_source('bigquery.gitcoin.project_lookup')
