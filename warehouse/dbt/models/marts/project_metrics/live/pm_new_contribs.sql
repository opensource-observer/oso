{# 
  
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
  d.project_id,
  d.repository_source AS namespace,
  CONCAT('NEW_CONTRIBUTORS_TOTAL_', tr.time_interval) AS impact_metric,
  COUNT(DISTINCT CASE
    WHEN DATE(d.date_first_contribution) >= tr.start_month
      THEN d.from_id
  END) AS amount
FROM {{ ref('int_devs') }} AS d
CROSS JOIN time_ranges AS tr
GROUP BY
  d.project_id,
  d.repository_source,
  tr.time_interval
