{#
  Gather all available event types (for the UI)
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT DISTINCT e.event_type
FROM {{ ref('int_events') }} AS e
