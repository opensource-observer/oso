MODEL (
  name oso.int_gharchive__repositories,
  description 'Repositories from GitHub Archive',
  dialect trino,
  kind FULL,
  partitioned_by DAY("valid_from"),
  grain (repo_id, repo_name, valid_from),
  tags (
    "github",
    "ddp"
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH repo_history AS (
  SELECT
    repo_id,
    repo_name,
    MIN(event_time) AS valid_from
  FROM oso.int_gharchive__github_events
  GROUP BY 1, 2
),
repo_history_with_valid_to AS (
  SELECT
    repo_id,
    repo_name,
    valid_from,
    -- CASE 1: Most recent name -> valid_to is NULL
    -- CASE 2: Has newer name -> valid_to is the valid_from of the next name
    LEAD(valid_from) OVER (
      PARTITION BY repo_id
      ORDER BY valid_from
    ) AS valid_to
  FROM repo_history
)

SELECT
  repo_id,
  repo_name,
  valid_from,
  valid_to
FROM repo_history_with_valid_to