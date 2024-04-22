{# 
  Address stats by project and network
#}

SELECT
  from_id,
  from_namespace AS network,
  project_id,
  MIN(bucket_day) AS date_first_txn,
  MAX(bucket_day) AS date_last_txn,
  SUM(amount) AS count_events
FROM {{ ref('int_user_events_daily_to_project') }}
WHERE event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY 1, 2, 3
