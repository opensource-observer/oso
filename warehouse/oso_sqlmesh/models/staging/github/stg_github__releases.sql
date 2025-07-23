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
    and ghe.created_at BETWEEN @start_dt  - INTERVAL '1' DAY AND @end_dt + INTERVAL '1' DAY
    and STRPTIME(ghe.payload ->> '$.release.created_at', '%Y-%m-%dT%H:%M:%SZ') BETWEEN @start_dt AND @end_dt
)
SELECT
  id AS id,
  -- the stg_github__events.created_at means the time the event was fired, but not the time the release was created
  -- so we need to use the release.created_at field from the payload
  STRPTIME(payload ->> '$.release.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
  repo.id AS repository_id,
  repo.name AS repository_name,
  actor.id AS actor_id,
  actor.login AS actor_login,
  'RELEASE_PUBLISHED' AS "type"
FROM release_events
