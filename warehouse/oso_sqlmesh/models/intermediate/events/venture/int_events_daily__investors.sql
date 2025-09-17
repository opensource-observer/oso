MODEL (
  name oso.int_events_daily__investors,
  description 'Intermediate table for venture investors',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "venture",
  ),
  enabled false,
);

SELECT
  bucket_day,
  event_source,
  event_type,
  investor_type,
  from_artifact_id,
  to_artifact_id
FROM oso.int_events_daily__coresignal_investors