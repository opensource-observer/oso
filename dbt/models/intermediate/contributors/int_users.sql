SELECT 
  e.project_id,
  e.from_id,
  TIMESTAMP_TRUNC(e.time, MONTH) AS bucket_month,
  CASE 
    WHEN SUM(e.amount) >= 1000 THEN 'HIGH_FREQUENCY_USER'
    WHEN SUM(e.amount) >= 10 THEN 'HIGH_VALUE_USER'
    ELSE 'LOW_VALUE_USER'
  END AS user_segment_type,
  1 AS amount
FROM {{ ref('int_events_to_project') }} as e
WHERE e.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY 1,2,3