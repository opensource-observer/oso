MODEL (
  name oso.int_repositories_all,
  description 'All GitHub repositories identified from GH Archive',
  kind SCD_TYPE_2_BY_TIME (
    unique_key artifact_source_id,
    updated_at_name last_commit_time
  ),
  start @github_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by DAY("first_commit_time"),
  grain (
    artifact_id,
    artifact_source_id,
    artifact_namespace,
    artifact_name,
    first_commit_time
  ),
  columns (
    artifact_id TEXT,
    artifact_source_id TEXT,
    artifact_namespace TEXT,
    artifact_name TEXT,
    first_commit_time TIMESTAMP,
    last_commit_time TIMESTAMP
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := first_commit_time,
      no_gap_date_part := 'day'
    )
  )
);

WITH new_events AS (
  SELECT
      to_artifact_id AS artifact_id,
      to_artifact_source_id AS artifact_source_id,
      to_artifact_namespace AS artifact_namespace,
      to_artifact_name AS artifact_name,
      time AS commit_time
  FROM  oso.int_events__github
  WHERE event_type = 'COMMIT_CODE'
    AND time BETWEEN @start_dt AND @end_dt
),

aggregated AS (
  SELECT
    ne.artifact_id,
    ne.artifact_source_id,
    ne.artifact_namespace,
    ne.artifact_name,
    LEAST(
      MIN(ne.commit_time),
      COALESCE(MIN(hist.first_commit_time), MIN(ne.commit_time))
    ) AS first_commit_time,
    MAX(ne.commit_time) AS last_commit_time
  FROM new_events AS ne
  LEFT JOIN @this_model AS hist
    ON hist.artifact_source_id = ne.artifact_source_id
    AND hist.artifact_id = ne.artifact_id
  GROUP BY
    ne.artifact_id,
    ne.artifact_source_id,
    ne.artifact_namespace,
    ne.artifact_name

SELECT
  artifact_id::TEXT,
  artifact_source_id::TEXT,
  artifact_namespace::TEXT,
  artifact_name::TEXT,
  first_commit_time::TIMESTAMP,
  last_commit_time::TIMESTAMP
FROM aggregated