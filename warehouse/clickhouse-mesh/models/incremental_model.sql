MODEL (
  name metrics.incremental_model,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 1
  ),
  start '2018-01-01',
  cron '@daily',
  grain (bucket_day, event_type)
);

SELECT
  time_bucket(INTERVAL 1 DAY, @start_date) as bucket_day,
  event_type,
  count(event_type) as events
FROM
  sources.int_events
WHERE
  time BETWEEN (@start_date - INTERVAL 30 DAY) AND @end_date
GROUP BY bucket_day, event_type
