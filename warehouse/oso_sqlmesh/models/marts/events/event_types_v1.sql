MODEL (
  name oso.event_types_v1,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'The `event_types_v1` table contains distinct event types from various sources, such as GitHub, blockchain, and funding events. This table is used to enumerate different types of events that occur across the open source ecosystem.',
  column_descriptions (
    event_type = 'The unique identifier for the event type, such as "COMMIT_CODE", "PULL_REQUEST_MERGED", or "FUNDING".'
  )
);

WITH all_event_types AS (
  SELECT
    event_type
  FROM oso.int_events_daily__github
  UNION ALL
  SELECT
    event_type
  FROM oso.int_events_daily__blockchain
  UNION ALL
  SELECT
    event_type
  FROM oso.int_events_daily__funding
)

SELECT DISTINCT
  events.event_type
FROM oso.int_events_daily__github AS events