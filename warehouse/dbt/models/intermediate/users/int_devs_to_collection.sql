{# 
  Developer stats by collection and repo source
#}

SELECT
  d.from_id,
  d.repository_source,
  pbc.collection_id,
  MIN(d.date_first_contribution) AS date_first_contribution,
  MAX(d.date_last_contribution) AS date_last_contribution,
  SUM(d.total_amount) AS total_amount
FROM {{ ref('int_devs_to_project') }} AS d
INNER JOIN {{ ref('int_projects_by_collection') }} AS pbc
  ON d.project_id = pbc.project_id
GROUP BY 1, 2, 3
