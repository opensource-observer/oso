{# 
  The most recent view of repositories from the github-resolve-repos cloudquery plugin.
#}
WITH most_recent_sync AS (
  SELECT MAX(_cq_sync_time) AS sync_time
  FROM {{ oso_source('ossd', 'repositories') }}
)

SELECT *
FROM {{ oso_source('ossd', 'repositories') }}
WHERE _cq_sync_time = (SELECT * FROM most_recent_sync)
