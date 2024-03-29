{# 
  All events daily to an artifact by source
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': False
  }) 
}}

SELECT
  e.to_id AS artifact_id,
  e.from_namespace,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
GROUP BY 1, 2, 3, 4
