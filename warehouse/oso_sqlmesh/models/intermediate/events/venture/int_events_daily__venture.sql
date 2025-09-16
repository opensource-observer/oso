MODEL (
  name oso.int_events_daily__venture,
  description 'Intermediate table for venture events',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "venture",
  ),
);


SELECT
  bucket_day,
  event_source,
  event_type,
  to_artifact_id,
  amount
FROM oso.int_events_daily__coresignal_venture