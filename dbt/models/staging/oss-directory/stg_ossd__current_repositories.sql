{# 
  The most recent view of repositories from the github-resolve-repos cloudquery plugin.
#}
WITH most_recent_sync AS (
  SELECT 
    MAX(_cq_sync_time) AS sync_time
  FROM `oso-production.opensource_observer.repositories_ossd`
)
SELECT 
  * 
FROM `oso-production.opensource_observer.repositories_ossd`
WHERE _cq_sync_time = (SELECT * FROM most_recent_sync)