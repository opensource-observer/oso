{# 
  All events monthly from a collection
#}

SELECT
  e.collection_id,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) as bucket_month,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_collection') }} AS e
WHERE e.collection_id IS NOT NULL
GROUP BY 1,2,3