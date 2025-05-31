MODEL (
  name oso.int_events_daily__ossd_funding,
  description 'Intermediate table for OSSD funding events',
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
    DATE_TRUNC('DAY', funding_date::DATE) AS bucket_day,
    'OSS_FUNDING' AS event_source,
    'FUNDING_AWARDED' AS event_type,
    @oso_entity_id('OSS_DIRECTORY', 'oso', to_project_name) AS to_artifact_id,
    @oso_entity_id('OSS_DIRECTORY', 'oso', from_funder_name) AS from_artifact_id,
    amount AS amount
  FROM oso.stg_ossd__current_funding
)

SELECT
  bucket_day::DATE AS bucket_day,
  event_source::VARCHAR AS event_source,
  event_type::VARCHAR AS event_type,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  SUM(amount)::DOUBLE AS amount
FROM events
GROUP BY 1, 2, 3, 4, 5