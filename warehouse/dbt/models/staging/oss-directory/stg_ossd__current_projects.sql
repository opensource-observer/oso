{# 
  The most recent view of projects from the ossd cloudquery plugin.
#}
WITH most_recent_sync AS (
  SELECT MAX(_cq_sync_time) AS sync_time
  FROM {{ oso_source('ossd', 'projects') }}
)

SELECT
  {# 
    id is the SHA256 of namespace + slug. We hardcode our namespace
    "oso" for now but we are assuming we will allow users to add their on the
    OSO website
  #}
  {{ oso_id('"oso"', 'slug') }} AS id,
  "oso" AS namespace,
  p.*
FROM {{ oso_source('ossd', 'projects') }} AS p
WHERE _cq_sync_time = (SELECT * FROM most_recent_sync)
