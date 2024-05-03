{#
  This model aggregates user events to project level by time interval.
  It is used to calculate various user engagement metrics by project.
#}

select
  e.from_id,
  e.from_namespace,
  e.project_id,
  t.time_interval,
  e.event_type,
  SUM(e.amount) as amount
from {{ ref('int_user_events_daily_to_project') }} as e
cross join {{ ref('int_time_intervals') }} as t
where DATE(e.bucket_day) >= t.start_date
group by
  e.from_id,
  e.project_id,
  e.from_namespace,
  t.time_interval,
  e.event_type
