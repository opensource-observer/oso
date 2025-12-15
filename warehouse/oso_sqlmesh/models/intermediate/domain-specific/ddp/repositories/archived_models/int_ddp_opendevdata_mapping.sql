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
    e.id AS ecosystem_id,
    e.name AS ecosystem_name,
    COUNT(DISTINCT er.repo_id) AS num_repos
  FROM oso.stg_opendevdata__ecosystems AS e
  JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS er
    ON e.id = er.ecosystem_id
  GROUP BY 1,2
),
repo_attributes AS (
  SELECT
    r.id AS odd_repo_id,
    LOWER(r.name) AS repo_name,
    r.is_blacklist AS is_blacklist,
    er.ecosystem_id AS ecosystem_id
  FROM oso.stg_opendevdata__repos AS r
  JOIN oso.stg_opendevdata__ecosystems_repos_recursive AS er
    ON r.id = er.repo_id
)
SELECT
  odd_repo_id,
  repo_name,
  MAX(is_blacklist) AS is_blacklist,
  MAX(CASE WHEN ecosystem_name = 'Ethereum' THEN True ELSE False END)
    AS is_ethereum,
  MAX_BY(ecosystem_name, num_repos) AS largest_ecosystem_name
FROM repo_attributes
JOIN ecos USING (ecosystem_id)
GROUP BY 1,2