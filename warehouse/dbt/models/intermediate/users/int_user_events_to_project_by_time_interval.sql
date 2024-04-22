{#
  This model aggregates user events to project level by time interval.
  It is used to calculate various user engagement metrics by project.
#}

SELECT
  e.from_id,
  e.from_namespace,
  e.project_id,
  t.time_interval,
  e.event_type,
  SUM(e.amount) AS amount
FROM {{ ref('int_user_events_daily_to_project') }} AS e
CROSS JOIN {{ ref('int_time_intervals') }} AS t
WHERE DATE(e.bucket_day) >= t.start_date
GROUP BY
  e.from_id,
  e.project_id,
  e.from_namespace,
  t.time_interval,
  e.event_type
