MODEL (
  name oso.stg_opendevdata__commits,
  description 'Staging model for opendevdata commits',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  repo_id::BIGINT AS repo_id,
  sha1::VARCHAR AS sha1,
  created_at::TIMESTAMP AS created_at,
  additions::BIGINT AS additions,
  deletions::BIGINT AS deletions,
  authored_at::TIMESTAMP AS authored_at,
  authored_at_offset::BIGINT AS authored_at_offset,
  committed_at::TIMESTAMP AS committed_at,
  committed_at_offset::BIGINT AS committed_at_offset,
  commit_author_name::VARCHAR AS commit_author_name,
  commit_author_email::VARCHAR AS commit_author_email,
  canonical_developer_id::BIGINT AS canonical_developer_id,
  is_bot::BIGINT AS is_bot
FROM @oso_source('bigquery.opendevdata.commits')
