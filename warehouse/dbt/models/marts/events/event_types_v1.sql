{#
  Gather all available event types (for the UI)
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT DISTINCT events.event_type
FROM {{ ref('int_events') }} AS events
