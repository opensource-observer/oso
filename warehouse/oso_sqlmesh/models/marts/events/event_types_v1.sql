MODEL (
  name oso.event_types_v1,
  kind FULL,
  tags (
    'export'
  )
);

SELECT DISTINCT
  events.event_type
FROM oso.int_events AS events