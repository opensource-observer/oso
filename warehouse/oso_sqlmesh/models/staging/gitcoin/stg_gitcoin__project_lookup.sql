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
  UPPER(source)::VARCHAR AS source,
  LOWER(group_id)::VARCHAR AS group_id,
  LOWER(project_id)::VARCHAR AS project_id
FROM @oso_source('bigquery.gitcoin.project_lookup')
