{# 
  All events monthly to a collection by source
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
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_collection_by_source') }} AS e
GROUP BY 1, 2, 3, 4
