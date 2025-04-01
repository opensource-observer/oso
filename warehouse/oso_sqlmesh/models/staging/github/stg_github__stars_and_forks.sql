MODEL (
  name oso.stg_github__stars_and_forks,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 7
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  dialect duckdb,
);

WITH watch_events AS (
  SELECT
    *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type IN ('WatchEvent', 'ForkEvent')
    and ghe.created_at BETWEEN @start_dt AND @end_dt
)
SELECT
  we.id AS id,
  we.created_at AS created_at,
  we.repo.id AS repository_id,
  we.repo.name AS repository_name,
  we.actor.id AS actor_id,
  we.actor.login AS actor_login,
  CASE we.type WHEN 'WatchEvent' THEN 'STARRED' WHEN 'ForkEvent' THEN 'FORKED' END AS "type"
FROM watch_events AS we