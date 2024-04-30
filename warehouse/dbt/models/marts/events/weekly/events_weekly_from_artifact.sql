{# 
  All events weekly from an artifact
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.artifact_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.bucket_day, WEEK) AS bucket_week,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_from_artifact') }} AS e
GROUP BY 1, 2, 3
