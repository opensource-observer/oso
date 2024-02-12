{# 
  All events daily to an artifact
#}

SELECT
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1,2,3,4,5