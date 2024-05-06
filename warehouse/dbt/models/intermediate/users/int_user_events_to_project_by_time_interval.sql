{#
  This model aggregates user events to project level by time interval.
  It is used to calculate various user engagement metrics by project.
#}

select
  int_user_events_daily_to_project.from_artifact_id,
  int_user_events_daily_to_project.event_source,
  int_user_events_daily_to_project.project_id,
  int_time_intervals.time_interval,
  int_user_events_daily_to_project.event_type,
  SUM(int_user_events_daily_to_project.amount) as amount
from {{ ref('int_user_events_daily_to_project') }}
cross join {{ ref('int_time_intervals') }}
where
  DATE(int_user_events_daily_to_project.bucket_day)
  >= int_time_intervals.start_date
group by
  int_user_events_daily_to_project.from_artifact_id,
  int_user_events_daily_to_project.project_id,
  int_user_events_daily_to_project.event_source,
  int_time_intervals.time_interval,
  int_user_events_daily_to_project.event_type
