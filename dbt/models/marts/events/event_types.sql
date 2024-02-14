{#
  Gather all available event types (for the UI)
#}
SELECT DISTINCT
  e.event_type
FROM {{ ref('int_events') }} as e