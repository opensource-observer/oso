MODEL (
  name oso.stg_github__releases,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  dialect duckdb,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

WITH release_events AS (
  SELECT
    *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'ReleaseEvent'
    and STRPTIME(ghe.payload ->> '$.release.created', '%Y-%m-%dT%H:%M:%SZ') BETWEEN @start_dt AND @end_dt
)
SELECT
  id AS id,
  STRPTIME(payload ->> '$.release.created', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
  repo.id AS repository_id,
  repo.name AS repository_name,
  actor.id AS actor_id,
  actor.login AS actor_login,
  'RELEASE_PUBLISHED' AS "type"
FROM release_events
