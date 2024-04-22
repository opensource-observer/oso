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
