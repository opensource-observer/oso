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
  TIMESTAMP_TRUNC(time, MONTH) AS bucket_month,
  COUNT(DISTINCT TIMESTAMP_TRUNC(time, DAY)) AS count_days,
  SUM(amount) AS amount
FROM {{ ref('int_events_to_project') }}
GROUP BY
  from_id,
  from_namespace,
  project_id,
  event_type,
  TIMESTAMP_TRUNC(time, MONTH)
