{# 
  This model calculates the total amount of events for each project and namespace
  for different time intervals. The time intervals are defined in the `time_intervals` tablint_events_to_project.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}

select
  int_events_to_project.project_id,
  int_time_intervals.time_interval,
  int_events_to_project.event_source,
  CONCAT(int_events_to_project.event_type, '_TOTAL') as impact_metric,
  SUM(int_events_to_project.amount) as amount
from {{ ref('int_events_to_project') }}
cross join {{ ref('int_time_intervals') }}
where DATE(int_events_to_project.time) >= int_time_intervals.start_date
group by
  int_events_to_project.project_id,
  int_time_intervals.time_interval,
  int_events_to_project.event_source,
  int_events_to_project.event_type
