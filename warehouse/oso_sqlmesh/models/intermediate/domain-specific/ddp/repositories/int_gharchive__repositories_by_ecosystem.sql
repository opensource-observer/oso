MODEL (
  name oso.int_gharchive__repositories_by_ecosystem,
  description 'GitHub repositories enriched with ecosystem information from OpenDevData',
  dialect trino,
  kind FULL,
  grain (repo_id),
  tags (
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  r.repo_id,
  e.name AS ecosystem_name,
  er.ecosystem_id,     
  r.opendevdata_id AS opendevdata_repo_id
FROM oso.int_opendevdata__repositories_with_repo_id AS r
JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS er
  ON r.opendevdata_id = er.repo_id
JOIN oso.stg_opendevdata__ecosystems AS e
  ON e.id = er.ecosystem_id