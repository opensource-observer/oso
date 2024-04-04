{# 
  All events daily from an artifact
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  e.from_id AS artifact_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_from_project') }} AS e
GROUP BY 1, 2, 3
