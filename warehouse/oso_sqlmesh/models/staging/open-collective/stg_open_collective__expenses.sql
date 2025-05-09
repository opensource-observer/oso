MODEL (
  name oso.stg_open_collective__expenses,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  partitioned_by (DAY("time"), "event_type"),
  start '2015-01-01',
  cron '@daily',
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
    ),
  )
);

SELECT
  created_at AS time,
  type AS event_type,
  id AS event_source_id,
  'OPEN_COLLECTIVE' AS event_source,
  @oso_entity_id(
    'OPEN_COLLECTIVE',
    JSON_EXTRACT_SCALAR(to_account, '$.slug'),
    JSON_EXTRACT_SCALAR(to_account, '$.name')
  ) AS to_artifact_id,
  JSON_EXTRACT_SCALAR(to_account, '$.name') AS to_name,
  JSON_EXTRACT_SCALAR(to_account, '$.slug') AS to_namespace,
  JSON_EXTRACT_SCALAR(to_account, '$.type') AS to_type,
  JSON_EXTRACT_SCALAR(to_account, '$.id') AS to_artifact_source_id,
  @oso_entity_id(
    'OPEN_COLLECTIVE',
    JSON_EXTRACT_SCALAR(from_account, '$.slug'),
    JSON_EXTRACT_SCALAR(from_account, '$.name')
  ) AS from_artifact_id,
  JSON_EXTRACT_SCALAR(from_account, '$.name') AS from_name,
  JSON_EXTRACT_SCALAR(from_account, '$.slug') AS from_namespace,
  JSON_EXTRACT_SCALAR(from_account, '$.type') AS from_type,
  JSON_EXTRACT_SCALAR(from_account, '$.id') AS from_artifact_source_id,
  ABS(CAST(JSON_EXTRACT_SCALAR(amount, '$.value') AS DOUBLE)) AS amount,
  JSON_EXTRACT_SCALAR(amount, '$.currency') AS unit
FROM @oso_source('bigquery.open_collective.expenses')