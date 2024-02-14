{#
  Gather all available event types (for the UI)
#}
SELECT DISTINCT
  e.type as event_type
FROM {{ ref('int_events') }} as e