MODEL (
  name metrics.event_types_v1,
  kind FULL,
  tags (
    'export'
  ),
);

select distinct events.event_type
from metrics.int_events as events