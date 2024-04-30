{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.collection_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_collection') }} AS e
GROUP BY 1, 2, 3
