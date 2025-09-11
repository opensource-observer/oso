MODEL (
  name oso.stg_l2beat__projects,
  description 'L2beat project information for various blockchain projects',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::VARCHAR AS id,
  name::VARCHAR AS name,
  slug::VARCHAR AS slug,
  type::VARCHAR AS type,
  host_chain::VARCHAR AS host_chain,
  category::VARCHAR AS category,
  is_archived::BOOLEAN AS is_archived,
  is_upcoming::BOOLEAN AS is_upcoming,
  is_under_review::BOOLEAN AS is_under_review,
  stage::VARCHAR AS stage,
  short_name::VARCHAR AS short_name
FROM @oso_source('bigquery.l2beat.projects')
