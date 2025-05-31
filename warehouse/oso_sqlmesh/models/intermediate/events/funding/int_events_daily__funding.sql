MODEL (
  name oso.int_events_daily__funding,
  description 'Intermediate table for funding events',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "funding",
  ),
);


WITH events AS (
  SELECT
    bucket_day,
    event_source,
    event_type,
    from_artifact_id,
    to_artifact_id,
    amount
  FROM oso.int_events_daily__gitcoin_funding
  UNION ALL
  SELECT
    bucket_day,
    event_source,
    event_type,
    from_artifact_id,
    to_artifact_id,
    amount
  FROM oso.int_events_daily__ossd_funding
  UNION ALL
  SELECT
    bucket_day,
    event_source,
    event_type,
    from_artifact_id,
    to_artifact_id,
    amount
  FROM oso.int_events_daily__open_collective_funding
)

SELECT
  bucket_day,
  event_source,
  event_type,
  from_artifact_id,
  to_artifact_id,
  amount
FROM events