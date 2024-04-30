{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.event_type,
  e.project_id,
  e.from_id AS artifact_id,
  MAX(e.time) AS event_time
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1, 2, 3
