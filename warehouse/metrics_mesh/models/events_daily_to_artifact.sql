MODEL (
  name metrics.events_daily_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 90
  ),
  start '2015-01-01',
  cron '@daily',
  dialect 'clickhouse',
  partitioned_by (event_type, DATE_TRUNC('MONTH', bucket_day)),
  grain (
    bucket_day,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id
  ),
  columns (
    bucket_day DATE,
    event_source String,
    event_type String,
    from_artifact_id String,
    to_artifact_id String,
    _sign Int8,
    _version UInt32,
    amount Float64
  ),
  physical_properties (
    ORDER_BY = (
      event_type,
      event_source,
      from_artifact_id,
      to_artifact_id,
      bucket_day
    ),
  ),
  storage_format "VersionedCollapsingMergeTree(_sign, _version)",
);
WITH events AS (
  SELECT DISTINCT from_artifact_id,
    to_artifact_id,
    event_source,
    event_type,
    time,
    amount
  from @oso_source.timeseries_events_by_artifact_v0
  where CAST(time AS DATE) between STR_TO_DATE(@start_ds, '%Y-%m-%d')::Date and STR_TO_DATE(@end_ds, '%Y-%m-%d')::Date
)
SELECT from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  1 as _sign,
  @str_to_unix_timestamp(@execution_ds) as _version,
  SUM(amount) AS amount
FROM events
GROUP BY from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE)