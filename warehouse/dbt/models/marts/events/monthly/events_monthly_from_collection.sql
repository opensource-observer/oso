{# 
  All events monthly from a collection
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_collection') }} AS e
WHERE e.collection_id IS NOT NULL
GROUP BY 1, 2, 3
