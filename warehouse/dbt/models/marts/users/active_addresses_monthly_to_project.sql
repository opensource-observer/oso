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
)


SELECT
  project_id,
  network,
  bucket_month,
  CASE
    WHEN is_new_user THEN 'NEW'
    ELSE 'RETURNING'
  END AS user_type,
  COUNT(DISTINCT from_id) AS amount
FROM activity_monthly
GROUP BY
  project_id,
  network,
  bucket_month,
  user_type
