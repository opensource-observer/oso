MODEL (
  name oso.stg_gitcoin__project_lookup,
  description "Staging table mapping Gitcoin project group to projects",
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  UPPER(source)::VARCHAR AS source,
  LOWER(group_id)::VARCHAR AS group_id,
  LOWER(project_id)::VARCHAR AS project_id
FROM @oso_source('bigquery.gitcoin.project_lookup')
