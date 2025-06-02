MODEL (
  name oso.int_events_daily__gitcoin_funding,
  description 'Intermediate table for Gitcoin funding events',
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
    DATE_TRUNC('DAY', time::DATE) AS bucket_day,
    event_source,
    'FUNDING_AWARDED' AS event_type,
    @oso_entity_id('OSS_DIRECTORY', 'oso', 'gitcoin') AS from_artifact_id,
    CASE
      WHEN oso_project_name IS NOT NULL
      THEN @oso_entity_id('OSS_DIRECTORY', 'oso', oso_project_name)
      /* TODO: Need a way to prevent collisions with Safe the project */
      ELSE @oso_entity_id('GITCOIN', '', recipient_address)
    END AS to_artifact_id,
    amount_in_usd
  FROM oso.int_events__gitcoin_funding
)

SELECT
  bucket_day::DATE AS bucket_day,
  event_source::VARCHAR AS event_source,
  event_type::VARCHAR AS event_type,
  from_artifact_id::VARCHAR AS from_artifact_id,
  to_artifact_id::VARCHAR AS to_artifact_id,
  SUM(amount_in_usd)::DOUBLE AS amount
FROM events
GROUP BY 1, 2, 3, 4, 5