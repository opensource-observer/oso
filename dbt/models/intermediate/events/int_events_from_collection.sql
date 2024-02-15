{# 
  All events from a collection
#}

SELECT
  pbc.collection_id,
  e.time,
  e.event_type,
  e.to_id,
  e.from_id,
  e.amount
FROM {{ ref('int_events_from_project') }} AS e
LEFT JOIN {{ ref('int_projects_by_collection') }} AS pbc
  ON pbc.project_id = e.project_id