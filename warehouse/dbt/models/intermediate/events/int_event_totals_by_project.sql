{# 
  This model calculates the total amount of events for each project and namespace
  for different time intervals. The time intervals are defined in the `time_intervals` table.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}

select
  e.project_id,
  e.event_source as artifact_source,
  t.time_interval,
  CONCAT(e.event_type, '_TOTAL') as impact_metric,
  SUM(e.amount) as amount
from {{ ref('int_events_to_project') }} as e
cross join {{ ref('int_time_intervals') }} as t
where DATE(e.time) >= t.start_date
group by e.project_id, e.event_source, t.time_interval, e.event_type
