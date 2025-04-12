MODEL (
  name oso.event_types_v1,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    number_of_rows(threshold := 0)
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