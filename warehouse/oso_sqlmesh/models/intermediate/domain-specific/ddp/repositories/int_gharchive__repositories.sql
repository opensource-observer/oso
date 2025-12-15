MODEL (
  name oso.int_gharchive__repositories,
  description 'Repositories from GitHub Archive',
  dialect trino,
  kind FULL,
  grain (repo_id, repo_name, valid_from),
  tags (
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  repo_id,
  repo_name,
  valid_from,
  lead(valid_from) OVER (
    PARTITION BY repo_id
    ORDER BY valid_from
  ) AS valid_to
FROM oso.int_gharchive__repo_name_change_log