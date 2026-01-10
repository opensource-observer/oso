MODEL (
  name oso.int_opendevdata__commits_with_repo_id,
  description 'OpenDevData commits enriched with canonical repo_id',
  dialect trino,
  kind FULL,
  partitioned_by DAY("created_at"),
  tags (
    "opendevdata",
    "ddp",
    "commits"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  odc.id,
  odc.repo_id AS opendevdata_repo_id,
  odc.sha1,
  odc.created_at,
  odc.additions,
  odc.deletions,
  odc.authored_at,
  odc.authored_at_offset,
  odc.committed_at,
  odc.committed_at_offset,
  odc.commit_author_name,
  odc.commit_author_email,
  odc.canonical_developer_id,
  odc.is_bot,
  odr.repo_id,
  ghc.repository_id AS github_repository_id
FROM oso.stg_opendevdata__commits AS odc
INNER JOIN oso.int_opendevdata__repositories_with_repo_id AS odr
  ON odc.repo_id = odr.opendevdata_id
LEFT JOIN oso.int_github__commits_all AS ghc
  ON odc.sha1 = ghc.sha
