MODEL (
  name oso.int_events_daily__coresignal_venture,
  description 'Intermediate table for Coresignal venture events',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "venture",
  ),
);

WITH events AS (
  SELECT
    DATE_TRUNC('DAY', announced_date::DATE) AS bucket_day,
    'CORESIGNAL' AS event_source,
    funding_round_name AS event_type,
    @oso_entity_id('CORESIGNAL', '', CAST(company_id AS VARCHAR)) AS to_artifact_id,
    amount_raised AS amount_in_usd
  FROM oso.stg_coresignal__funding_rounds
)

SELECT
  bucket_day::DATE AS bucket_day,
  event_source::VARCHAR AS event_source,
  event_type::VARCHAR AS event_type,
  to_artifact_id::VARCHAR AS to_artifact_id,
  MAX(amount_in_usd)::DOUBLE AS amount -- We have multiple rows per event due to multiple investors
FROM events
GROUP BY 1, 2, 3, 4