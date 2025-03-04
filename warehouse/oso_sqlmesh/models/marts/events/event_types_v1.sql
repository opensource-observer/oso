model(name oso.event_types_v1, kind full, tags('export'),)
;

select distinct events.event_type
from oso.int_events as events
