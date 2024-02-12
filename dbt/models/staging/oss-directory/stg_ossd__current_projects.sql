{# 
  The most recent view of projects from the ossd cloudquery plugin.
#}
WITH most_recent_sync AS (
  SELECT 
    MAX(_cq_sync_time) AS sync_time
  FROM `oso-production.opensource_observer.projects_ossd`
)
SELECT 
  * 
FROM `oso-production.opensource_observer.projects_ossd`
WHERE _cq_sync_time = (SELECT * FROM most_recent_sync)