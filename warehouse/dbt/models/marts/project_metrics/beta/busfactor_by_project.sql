{#

  This model calculates the bus factor for each project in the database. The bus factor is a metric that
  measures the number of contributors that are responsible for at least 50% of the contributions to a project
  over a given time period. 

  The `contributions` CTE calculates the total amount of contributions for each contributor to each project.
  The `project_periods` CTE calculates the start and end month for each project.
  The `aggregated_contributions` CTE calculates the total amount of contributions for each contributor to each project
  for different time periods (90 days, 6 months, 1 year, and all time).
  The `ranked_contributions` CTE calculates the rank of each contributor for each project and time period, as well as the
  total amount of contributions for each project and time period. The final select statement calculates the bus factor
  for each project and time period by selecting the maximum rank of contributors whose cumulative contributions are
  greater than or equal to 50% of the total contributions to the project.

  More information on the bus factor can be found here: https://chaoss.community/kb/metric-bus-factor/

#}

WITH all_contributions AS (
  SELECT
    project_id,
    from_id,
    SUM(amount) AS total_amount,
    DATE_TRUNC(DATE(time), MONTH) AS contribution_month
  FROM {{ ref('int_events_to_project') }}
  WHERE event_type = 'COMMIT_CODE' -- CONTRIBUTION FILTER
  GROUP BY
    project_id,
    from_id,
    DATE_TRUNC(DATE(time), MONTH)
),

contributions AS (
  SELECT *
  FROM all_contributions
  WHERE total_amount < 1000 -- BOT FILTER
),

project_periods AS (
  SELECT
    project_id,
    MIN(contribution_month) AS start_month,
    MAX(contribution_month) AS end_month
  FROM contributions
  GROUP BY project_id
),

aggregated_contributions AS (
  SELECT
    c.project_id,
    c.from_id,
    SUM(c.total_amount) AS total_amount,
    '90D' AS period
  FROM contributions AS c
  INNER JOIN project_periods AS p ON c.project_id = p.project_id
  WHERE c.contribution_month > DATE_SUB(p.end_month, INTERVAL 3 MONTH)
  GROUP BY
    c.project_id,
    c.from_id
  UNION ALL
  SELECT
    c.project_id,
    c.from_id,
    SUM(c.total_amount) AS total_amount,
    '6M' AS period
  FROM contributions AS c
  INNER JOIN project_periods AS p ON c.project_id = p.project_id
  WHERE c.contribution_month > DATE_SUB(p.end_month, INTERVAL 6 MONTH)
  GROUP BY
    c.project_id,
    c.from_id
  UNION ALL
  SELECT
    c.project_id,
    c.from_id,
    SUM(c.total_amount) AS total_amount,
    '1Y' AS period
  FROM contributions AS c
  INNER JOIN project_periods AS p ON c.project_id = p.project_id
  WHERE c.contribution_month > DATE_SUB(p.end_month, INTERVAL 12 MONTH)
  GROUP BY
    c.project_id,
    c.from_id
  UNION ALL
  SELECT
    c.project_id,
    c.from_id,
    SUM(c.total_amount) AS total_amount,
    'ALL' AS period
  FROM contributions AS c
  GROUP BY
    c.project_id,
    c.from_id
),

ranked_contributions AS (
  SELECT
    project_id,
    period,
    from_id,
    total_amount,
    RANK()
      OVER (
        PARTITION BY project_id, period ORDER BY total_amount DESC
      ) AS rank,
    SUM(total_amount)
      OVER (
        PARTITION BY project_id, period
      ) AS total_project_amount,
    SUM(total_amount)
      OVER (
        PARTITION BY project_id, period
        ORDER BY total_amount DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
      ) AS cumulative_amount
  FROM aggregated_contributions
)

SELECT
  project_id,
  CONCAT('BUSFACTOR_', period) AS impact_metric,
  MAX(
    CASE
      WHEN cumulative_amount <= total_project_amount * 0.5
        THEN rank
      ELSE 1
    END
  ) AS amount
FROM
  ranked_contributions
GROUP BY
  project_id,
  period
