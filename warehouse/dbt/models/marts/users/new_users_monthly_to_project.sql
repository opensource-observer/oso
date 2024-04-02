{#
  Monthly new vs returning users by project and namespace
#}

WITH user_data AS (
  SELECT
    from_id,
    repository_source AS namespace,
    project_id,
    DATE_TRUNC(DATE(date_first_contribution), MONTH) AS month_first
  FROM {{ ref('int_devs_to_project') }}
  UNION ALL
  SELECT
    from_id,
    network AS namespace,
    project_id,
    DATE_TRUNC(DATE(date_first_txn), MONTH) AS month_first
  FROM {{ ref('int_addresses_to_project') }}
)

SELECT
  e.from_id,
  e.from_id AS namespace,
  e.project_id,
  e.bucket_month,
  CASE
    WHEN e.bucket_month = u.month_first THEN 'new'
    ELSE 'returning'
  END AS user_status
FROM {{ ref('int_user_events_monthly_to_project') }} AS e
LEFT JOIN user_data AS u
  ON
    e.from_id = u.from_id
    AND e.from_namespace = u.namespace
    AND e.project_id = u.project_id
