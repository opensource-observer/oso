{#
  Gather all available event types (for the UI)
#}
SELECT DISTINCT
  e.type
FROM {{ ref('int_events') }} as e