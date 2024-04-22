{#
  Monthly active addresses to project by network
#}


WITH activity AS (
  SELECT
    project_id,
    from_namespace AS network,
    from_id,
    DATE_TRUNC(bucket_day, MONTH) AS bucket_month,
    (address_type = 'NEW') AS is_new_user
  FROM {{ ref('int_addresses_daily_activity') }}
),

activity_monthly AS (
  SELECT
    project_id,
    network,
    from_id,
    bucket_month,
    MAX(is_new_user) AS is_new_user
  FROM activity
  GROUP BY 1, 2, 3, 4
),

user_classification AS (
  SELECT
    project_id,
    network,
    bucket_month,
    from_id,
    CASE
      WHEN is_new_user THEN 'NEW'
      ELSE 'RETURNING'
    END AS user_type
  FROM activity_monthly
)

SELECT
  project_id,
  network,
  bucket_month,
  user_type,
  COUNT(DISTINCT from_id) AS amount
FROM user_classification
GROUP BY 1, 2, 3, 4
