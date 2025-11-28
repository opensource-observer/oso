MODEL (
  name oso.stg_opendevdata__repos,
  description 'Staging model for opendevdata repos',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  created_at::TIMESTAMP AS created_at,
  repo_created_at::TIMESTAMP AS repo_created_at,
  name::VARCHAR AS name,
  github_graphql_id::VARCHAR AS github_graphql_id,
  link::VARCHAR AS link,
  organization_id::BIGINT AS organization_id,
  num_stars::BIGINT AS num_stars,
  num_forks::BIGINT AS num_forks,
  num_issues::BIGINT AS num_issues,
  is_blacklist::BIGINT AS is_blacklist
FROM @oso_source('bigquery.opendevdata.repos')
