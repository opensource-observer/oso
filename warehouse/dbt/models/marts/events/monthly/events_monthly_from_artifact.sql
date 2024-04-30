{# 
  All events monthly from an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.artifact_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) AS bucket_month,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_artifact') }} AS e
GROUP BY 1, 2, 3
