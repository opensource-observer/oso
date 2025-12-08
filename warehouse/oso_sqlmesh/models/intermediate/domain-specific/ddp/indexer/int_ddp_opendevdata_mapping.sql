MODEL (
  name oso.int_ddp_opendevdata_mapping,
  description 'Intermediate model for mapping OpenDevData ecosystems labels to DDP',
  dialect trino,
  kind FULL,
  grain (odd_repo_id, repo_name),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ecos AS (
  SELECT
    ecosystem_id,
    COUNT(DISTINCT repo_id) AS num_repos
  FROM oso.int_opendevdata_ecosystem_repos
  GROUP BY 1
)
SELECT
  repo_id AS odd_repo_id,
  repo_name AS repo_name,
  is_blacklist AS odd_is_blacklist,
  MAX(CASE WHEN ecosystem_name = 'Ethereum' THEN True ELSE False END)
    AS is_ethereum,
  MAX_BY(ecosystem_name, num_repos) AS largest_ecosystem_name
FROM oso.int_opendevdata_ecosystem_repos
JOIN ecos USING (ecosystem_id)
GROUP BY 1,2,3