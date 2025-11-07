MODEL (
  name oso.int_events_monthly__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_month,
    batch_size 365,
    batch_concurrency 2,
    lookback @default_daily_incremental_lookback,
    forward_only true,
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_month"), "event_type"),
  grain (bucket_month, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_month,
      no_gap_date_part := 'month',
    ),
  ),
  tags (
    "github",
    "incremental",
  )
);

SELECT
  DATE_TRUNC('MONTH', bucket_day::DATE) AS bucket_month,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  event_source::VARCHAR,
  event_type::VARCHAR,
  SUM(amount::DOUBLE)::DOUBLE AS amount
FROM oso.int_events_daily__github as events
WHERE bucket_day BETWEEN @start_dt AND @end_dt
GROUP BY
  DATE_TRUNC('MONTH', bucket_day::DATE),
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type