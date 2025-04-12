MODEL (
  name oso.int_events__dependencies,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id),
  enabled false,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(event_source_name, 'DEPS_DEV');

WITH artifacts AS (
  SELECT
    artifact_name
  FROM oso.int_all_artifacts
  WHERE
    artifact_source = 'NPM'
), snapshots AS (
  SELECT
    snapshotat AS time,
    system AS from_artifact_type,
    name AS from_artifact_name,
    version AS from_artifact_version,
    dependency.name AS to_artifact_name,
    dependency.system AS to_artifact_type,
    dependency.version AS to_artifact_version,
    LAG(dependency.name) OVER (PARTITION BY system, name, dependency.name, version, dependency.version ORDER BY snapshotat) AS previous_to_artifact_name
  FROM @oso_source('bigquery.oso.stg_deps_dev__dependencies')
  WHERE
    minimumdepth = 1
    AND dependency.name IN (
      SELECT
        artifact_name
      FROM artifacts
    )
    AND /* We only need to lag over a short period because snapshots are duplicated */ /* data. Using 60 to ensure we capture the previous snapshot. */ snapshotat BETWEEN @start_date - INTERVAL '60' DAY AND @end_date
), intermediate AS (
  SELECT
    time,
    CASE
      WHEN previous_to_artifact_name IS NULL
      THEN 'ADD_DEPENDENCY'
      WHEN NOT to_artifact_name IS NULL AND to_artifact_name <> previous_to_artifact_name
      THEN 'REMOVE_DEPENDENCY'
      ELSE 'NO_CHANGE'
    END AS event_type,
    @event_source_name AS event_source,
    @deps_parse_name(to_artifact_type, to_artifact_name) AS to_artifact_name,
    @deps_parse_namespace(to_artifact_type, to_artifact_name) AS to_artifact_namespace,
    to_artifact_type,
    @deps_parse_name(from_artifact_type, from_artifact_name) AS from_artifact_name,
    @deps_parse_namespace(from_artifact_type, from_artifact_name) AS from_artifact_namespace,
    from_artifact_type,
    1.0 AS amount
  FROM snapshots
), artifact_ids AS (
  SELECT
    time,
    event_type,
    event_source,
    @oso_entity_id(event_source, to_artifact_namespace, to_artifact_name) AS to_artifact_id,
    to_artifact_name,
    to_artifact_namespace,
    to_artifact_type,
    -- TODO: review if this is correct
    @oso_id(event_source, to_artifact_type) AS to_artifact_source_id,
    @oso_entity_id(event_source, from_artifact_namespace, from_artifact_name) AS from_artifact_id,
    from_artifact_name,
    from_artifact_namespace,
    from_artifact_type,
    -- TODO: review if this is correct
    @oso_id(event_source, from_artifact_type) AS from_artifact_source_id,
    amount
  FROM intermediate
  WHERE
    event_type <> 'NO_CHANGE'
), changes AS (
  SELECT
    time,
    event_type,
    event_source,
    to_artifact_id,
    to_artifact_name,
    to_artifact_namespace,
    to_artifact_type,
    to_artifact_source_id,
    from_artifact_id,
    from_artifact_name,
    from_artifact_namespace,
    from_artifact_type,
    from_artifact_source_id,
    amount,
    @oso_id(
      event_source,
      time,
      to_artifact_id,
      to_artifact_type,
      from_artifact_id,
      from_artifact_type,
      event_type
    ) AS event_source_id
  FROM artifact_ids
)
SELECT
  time,
  to_artifact_id,
  from_artifact_id,
  UPPER(event_type) AS event_type,
  event_source_id::VARCHAR AS event_source_id,
  UPPER(event_source) AS event_source,
  LOWER(to_artifact_name) AS to_artifact_name,
  LOWER(to_artifact_namespace) AS to_artifact_namespace,
  UPPER(to_artifact_type) AS to_artifact_type,
  LOWER(to_artifact_source_id) AS to_artifact_source_id,
  LOWER(from_artifact_name) AS from_artifact_name,
  LOWER(from_artifact_namespace) AS from_artifact_namespace,
  UPPER(from_artifact_type) AS from_artifact_type,
  LOWER(from_artifact_source_id) AS from_artifact_source_id,
  amount::DOUBLE AS amount
FROM changes