{# 
  Address stats by collection and network
#}

SELECT
  a.from_id,
  a.network,
  pbc.collection_id,
  MIN(a.date_first_txn) AS date_first_txn,
  MAX(a.date_last_txn) AS date_last_txn,
  SUM(a.total_amount) AS total_amount
FROM {{ ref('int_addresses_to_project') }} AS a
INNER JOIN {{ ref('int_projects_by_collection') }} AS pbc
  ON a.project_id = pbc.project_id
GROUP BY 1, 2, 3
