MODEL (
  name oso.int_gharchive__repo_name_change_log,
  description 'Append-only log of repo_name change points (first-seen or rename). One row per change.',
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column valid_from,
    batch_size 120,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by MONTH("valid_from"),
  grain (repo_id, repo_name, valid_from),
  columns (
    repo_id BIGINT,
    repo_name TEXT,
    valid_from TIMESTAMP
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := valid_from,
      no_gap_date_part := 'day',
    ),
  ),
  tags (
    "github",
    "incremental",
  )
);

-- Get the last known repo_name for each repo_id from previous batches
-- CRITICAL: Only query historical data (before @start_dt) to respect incremental boundaries
-- This ensures we get the state at the start of the current batch without reading
-- data that's being processed in this same incremental run
WITH last_known AS (
  SELECT repo_id, repo_name AS last_repo_name
  FROM (
    SELECT
      repo_id,
      repo_name,
      valid_from,
      row_number() OVER (PARTITION BY repo_id ORDER BY valid_from DESC) AS rn
    FROM oso.int_gharchive__repo_name_change_log
    WHERE valid_from < @start_dt  -- Only historical data before current batch
  ) t
  WHERE rn = 1
),
-- Get events from the current batch time range
batch_events AS (
  SELECT
    repo_id,
    repo_name,
    event_time
  FROM oso.int_gharchive__github_events
  WHERE event_time BETWEEN @start_dt AND @end_dt
    AND repo_id IS NOT NULL
    AND repo_name IS NOT NULL
),
-- Determine the previous repo_name for each event in the batch
-- Algorithm:
--   1. Use LAG to get the previous repo_name within the current batch
--   2. For the first event of a repo_id in the batch, LAG returns NULL
--   3. COALESCE with last_repo_name from historical data to bridge across batches
--      This is necessary for incremental processing: we need to know what the
--      repo_name was at the end of the previous batch to detect renames correctly
ordered AS (
  SELECT
    e.repo_id,
    e.repo_name,
    e.event_time,
    coalesce(
      lag(e.repo_name) OVER (PARTITION BY e.repo_id ORDER BY e.event_time),
      lk.last_repo_name
    ) AS prev_repo_name
  FROM batch_events e
  LEFT JOIN last_known lk
    ON e.repo_id = lk.repo_id
),
-- Detect change points: when repo_name changes or is first seen
-- Change detection logic:
--   - prev_repo_name IS NULL: First time we've seen this repo_name (first occurrence)
--   - repo_name <> prev_repo_name: Repository was renamed (name changed)
-- Both cases indicate a change point that should be recorded
change_points AS (
  SELECT
    repo_id,
    repo_name,
    min(event_time) AS valid_from
  FROM ordered
  WHERE prev_repo_name IS NULL OR repo_name <> prev_repo_name
  GROUP BY repo_id, repo_name
)
SELECT
  repo_id,
  repo_name,
  valid_from
FROM change_points