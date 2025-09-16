MODEL (
  name oso.int_events_daily__coresignal_investors,
  description 'Intermediate table for Coresignal venture investors',
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
    'LEAD' AS investor_type,
    @oso_entity_id('CORESIGNAL', '', lead_investor) AS from_artifact_id,
    @oso_entity_id('CORESIGNAL', '', CAST(company_id AS VARCHAR)) AS to_artifact_id
  FROM oso.stg_coresignal__funding_rounds
)

SELECT
  bucket_day::DATE AS bucket_day,
  event_source::VARCHAR AS event_source,
  event_type::VARCHAR AS event_type,
  investor_type::VARCHAR AS investor_type,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id
FROM events