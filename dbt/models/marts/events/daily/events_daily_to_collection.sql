SELECT
  e.collection_id,
  TIMESTAMP_TRUNC(e.time, DAY) as bucket_day,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_collection') }} AS e
GROUP BY 1,2,3