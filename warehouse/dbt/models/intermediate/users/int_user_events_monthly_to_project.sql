{#
  This model aggregates user events to project level on
  a monthly basis. It is used to calculate various 
  user engagement metrics by project.
#}

SELECT
  from_id,
  from_namespace,
  project_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, MONTH) AS bucket_month,
  COUNT(DISTINCT bucket_day) AS count_days,
  SUM(amount) AS total_amount
FROM {{ ref('int_user_events_daily_to_project') }}
GROUP BY
  from_id,
  from_namespace,
  project_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, MONTH)
