MODEL (
  name oso.stg_opendevdata__ecosystems,
  description 'Staging model for opendevdata ecosystems',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  launch_date::DATE AS launch_date,
  earliest_first_party_commit_date::DATE AS earliest_first_party_commit_date,
  earliest_first_party_repo_id::BIGINT AS earliest_first_party_repo_id,
  earliest_repo_commit_date::DATE AS earliest_repo_commit_date,
  earliest_repo_id::BIGINT AS earliest_repo_id,
  derived_launch_date::DATE AS derived_launch_date,
  name::VARCHAR AS name,
  is_crypto::BIGINT AS is_crypto,
  is_category::BIGINT AS is_category,
  is_virtual::BIGINT AS is_virtual,
  is_chain::BIGINT AS is_chain,
  is_multichain::BIGINT AS is_multichain
FROM @oso_source('bigquery.opendevdata.ecosystems')
