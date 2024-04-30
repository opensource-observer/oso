{# 
  All events daily from a project
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  e.project_id,
  e.event_type,
  TIMESTAMP_TRUNC(e.time, DAY) AS bucket_day,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_from_project') }} AS e
WHERE e.project_id IS NOT NULL
GROUP BY 1, 2, 3
