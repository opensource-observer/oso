{# 
  This model calculates the total amount of events for each project and namespace
  for different time intervals. The time intervals are defined in the `time_intervals` table.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}

SELECT
  e.project_id,
  e.to_namespace AS artifact_namespace,
  t.time_interval,
  CONCAT(e.event_type, '_TOTAL') AS impact_metric,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
CROSS JOIN {{ ref('int_time_intervals') }} AS t
WHERE DATE(e.time) >= t.start_date
GROUP BY e.project_id, e.to_namespace, t.time_interval, e.event_type
