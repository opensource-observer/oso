{# 
  Address stats by project and network
#}

SELECT
  e.project_id,
  e.from_namespace,
  e.from_id,
  e.bucket_day,
  e.amount,
  CASE
    WHEN e.bucket_day = a.date_first_txn THEN 'NEW'
    ELSE 'RETURNING'
  END AS address_type
FROM {{ ref('int_user_events_daily_to_project') }} AS e
LEFT JOIN {{ ref('int_addresses') }} AS a
  ON
    e.from_id = a.from_id
    AND e.from_namespace = a.network
    AND e.project_id = a.project_id
WHERE
  e.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
