MODEL (
  name oso.stg_github__pull_requests_since_20251007,
  description 'Turns all watch events into push events (version after 2025-10-07)',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column event_time,
    batch_size 90,
    batch_concurrency 3,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  dialect "duckdb",
  start @github_events_v20251007_start_date,
  partitioned_by DAY(event_time),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := event_time,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "incremental"
  )
);

WITH pull_request_events AS (
  SELECT
    *
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'PullRequestEvent'
    -- We cast a wider net of pull request events to ensure we capture any
    -- random changes for a single pullrequest in a given time range
    and ghe.created_at BETWEEN @start_dt  - INTERVAL '1' DAY AND @end_dt + INTERVAL '1' DAY
)
SELECT
  pre.id AS id,
  -- TODO: Get the real details from the REST api for created_at
  pre.created_at AS event_time,
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  pre.actor.id AS actor_id,
  pre.actor.login AS actor_login,
  CONCAT('PULL_REQUEST_', UPPER(pre.payload ->> '$.action')) AS "type",
  CAST(pre.payload -> '$.number' AS BIGINT) AS "number",
  -- TODO: Get created_at by API
  pre.created_at AS created_at,
  -- TODO: Get merged_at, closed_at, state, comments, author_association by API
  -- These fields were removed from the PullRequestEvent payload in v2 data.
  CAST(NULL AS TIMESTAMP) AS merged_at,
  CAST(NULL AS TIMESTAMP) AS closed_at,
  CAST(NULL AS VARCHAR) AS "state",
  CAST(NULL AS DOUBLE) AS comments,
  CAST(NULL AS VARCHAR) AS author_association
FROM pull_request_events AS pre
