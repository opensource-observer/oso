{# 
  All events to a collection
#}

SELECT
  e.*,
  pbc.collection_id
FROM {{ ref('int_events_to_project') }} AS e
INNER JOIN {{ ref('int_projects_by_collection') }} AS pbc
  ON e.project_id = pbc.project_id
