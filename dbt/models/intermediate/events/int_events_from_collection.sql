{# 
  All events from a collection
#}

SELECT
  e.*,
  pbc.collection_id
FROM {{ ref('int_events_from_project') }} AS e
LEFT JOIN {{ ref('int_projects_by_collection') }} AS pbc
  ON e.project_id = pbc.project_id
