MODEL (
  name oso.int_events_daily__coresignal_venture,
  description 'Aggregated daily CoreSignal venture funding events',
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
  DATE_TRUNC('DAY', time::DATE) AS bucket_day,
  event_source::VARCHAR AS event_source,
  event_type::VARCHAR AS event_type,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  SUM(amount_raised::DOUBLE) AS amount
FROM oso.int_events__coresignal_venture
WHERE
  event_type = 'INVESTMENT_RECEIVED'
  AND amount_raised_currency = 'USD'
  AND to_oso_project_name IS NOT NULL
GROUP BY 1, 2, 3, 4, 5