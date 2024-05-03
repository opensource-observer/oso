{#
  Gather all available event types (for the UI)
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select distinct events.event_type
from {{ ref('int_events') }} as events
