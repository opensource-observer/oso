-- Blockchain events (currently only from the superchain dataset)
MODEL (
  name oso.int_events_daily__blockchain,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 180,
    batch_concurrency 1
  ),
  start '2021-10-01',
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type", "event_source"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

SELECT
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  event_source::VARCHAR,
  SUM(gas_used::DOUBLE * gas_price_tx::DOUBLE)::DOUBLE AS amount,
  COUNT(DISTINCT transaction_hash)::DOUBLE AS "count"
FROM oso.int_events__blockchain as events
GROUP BY
  from_artifact_id,
  to_artifact_id,
  event_source,
  event_type,
  DATE_TRUNC('DAY', time::DATE)
