{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

WITH users AS (
  SELECT
    project_id,
    from_namespace,
    event_type,
    bucket_month,
    COUNT(DISTINCT from_id) AS amount
  FROM {{ ref('int_user_events_monthly_to_project') }}
  GROUP BY 1, 2, 3, 4
)

SELECT
  project_id,
  'Developers' AS user_segment_type,
  bucket_month,
  amount
FROM users
WHERE event_type = 'COMMIT_CODE'
UNION ALL
SELECT
  project_id,
  'Active Addresses' AS user_segment_type,
  bucket_month,
  amount
FROM users
WHERE event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
