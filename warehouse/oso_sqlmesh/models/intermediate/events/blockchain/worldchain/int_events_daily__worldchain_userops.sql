MODEL (
  name oso.int_events_daily__worldchain_userops,
  description 'Worldchain user events',
  kind incremental_by_time_range(
   time_column bucket_day,
   batch_size 60,
   batch_concurrency 3,
   lookback 31
  ),
  start '2024-09-01',
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type", "event_source"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmusthaveforwardonly",
    "incrementalmustdefinenogapsaudit",
  )
);

SELECT
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  event_source::VARCHAR,
  event_type::VARCHAR,
  SUM(userop_gas_cost)::DOUBLE AS amount,
  COUNT(*)::DOUBLE AS "count"
FROM oso.int_events__worldchain_userops as events
WHERE time BETWEEN @start_dt AND @end_dt
GROUP BY
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE)