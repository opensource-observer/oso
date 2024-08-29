MODEL (
  name metrics.incremental_model,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 1
  ),
  start '2024-08-01',
  cron '@daily',
  dialect 'clickhouse',
  columns (
    bucket_day Date, 
    event_type String,
    events Int64,
  )
);

SELECT
  @day_bucket(@start_date) as bucket_day,
  CASE WHEN event_type IS NULL THEN '' ELSE event_type END as event_type,
  count(event_type) as events,
FROM
  @source("oso", "int_events") as test
WHERE
  time BETWEEN (@start_date - INTERVAL 30 DAY) AND @end_date
GROUP BY bucket_day, event_type
