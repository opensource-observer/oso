{# 
  This model calculates the total amount of events for each project and namespace
  for different time intervals. The time intervals are defined in the `time_intervals` table.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  e.project_id,
  e.from_namespace AS namespace,
  t.time_interval,
  CONCAT(e.event_type, '_TOTAL') AS impact_metric,
  SUM(e.amount) AS amount
FROM {{ ref('events_daily_to_project_by_source') }} AS e
CROSS JOIN {{ ref('int_time_intervals') }} AS t
WHERE DATE(e.bucket_day) >= t.start_date
GROUP BY e.project_id, e.from_namespace, t.time_interval, e.event_type
