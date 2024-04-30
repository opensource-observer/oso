{# 
  All events monthly to a collection
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_collection') }} AS e
GROUP BY 1, 2, 3
