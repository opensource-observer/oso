MODEL (
  name oso.stg_opendevdata__repo_developer_activities,
  description 'Staging model for opendevdata repo_developer_activities',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  ecosystem_id::BIGINT AS ecosystem_id,
  repo_id::BIGINT AS repo_id,
  day::DATE AS day,
  canonical_developer_id::BIGINT AS canonical_developer_id,
  num_commits::BIGINT AS num_commits,
  is_explicit::BOOLEAN AS is_explicit,
  is_chain::BIGINT AS is_chain,
  is_direct_exclusive::BOOLEAN AS is_direct_exclusive,
  is_indirect_exclusive::BOOLEAN AS is_indirect_exclusive,
  exclusive_at_connection::BOOLEAN AS exclusive_at_connection,
  exclusive_till::DATE AS exclusive_till
FROM @oso_source('bigquery.opendevdata.repo_developer_activities')
