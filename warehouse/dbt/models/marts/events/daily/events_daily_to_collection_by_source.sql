{# 
  All events daily to a collection by source
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': False
  }) 
}}

SELECT
  e.collection_id,
  e.from_namespace,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_collection') }} AS e
GROUP BY 1, 2, 3, 4
