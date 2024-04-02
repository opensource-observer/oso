{# 
  This model calculates the total amount of events for each project and namespace
  for different time intervals. The time intervals are defined in the `time_ranges` CTE.
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

WITH time_ranges AS (
  SELECT
    time_interval,
    DATE_TRUNC(start_date, MONTH) AS start_month
  FROM (
    SELECT
      '30D' AS time_interval,
      DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AS start_date
    UNION ALL
    SELECT
      '90D' AS time_interval,
      DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) AS start_date
    UNION ALL
    SELECT
      '6M' AS time_interval,
      DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH) AS start_date
    UNION ALL
    SELECT
      '1Y' AS time_interval,
      DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR) AS start_date
    UNION ALL
    SELECT
      'ALL' AS time_interval,
      DATE('1970-01-01') AS start_date
  )
)

SELECT
  e.project_id,
  e.repository_source AS namespace,
  CONCAT(e.user_segment_type, '_TOTAL_', tr.time_interval) AS impact_metric,
  SUM(e.amount) AS amount
FROM {{ ref('active_devs_monthly_to_project') }} AS e
CROSS JOIN time_ranges AS tr
WHERE
  DATE(e.bucket_month) >= tr.start_month
  AND DATE(e.bucket_month) < DATE_TRUNC(CURRENT_DATE(), MONTH)
GROUP BY
  e.project_id,
  e.repository_source,
  e.user_segment_type,
  tr.time_interval
