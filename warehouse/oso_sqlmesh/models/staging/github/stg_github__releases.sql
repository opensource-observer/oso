MODEL (
  name oso.stg_github__releases,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 7
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH release_events AS (
  SELECT
    *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'ReleaseEvent'
    and ghe.created_at BETWEEN @start_dt AND @end_dt
)
SELECT
  id AS id,
  created_at AS created_at,
  repo.id AS repository_id,
  repo.name AS repository_name,
  actor.id AS actor_id,
  actor.login AS actor_login,
  'RELEASE_PUBLISHED' AS "type"
FROM release_events