{# 
  The most recent view of repositories from the github-resolve-repos cloudquery plugin.
#}
WITH most_recent_sync AS (
  SELECT 
    MAX(_cq_sync_time) AS sync_time
  FROM {{ source('ossd', 'repositories')}} as p
)
SELECT 
  * 
FROM {{ source('ossd', 'repositories')}} as p
WHERE _cq_sync_time = (SELECT * FROM most_recent_sync)