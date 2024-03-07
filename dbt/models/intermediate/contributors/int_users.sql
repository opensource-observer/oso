SELECT
  e.project_id,
  e.to_namespace AS onchain_network,
  e.from_id,
  1 AS amount,
  TIMESTAMP_TRUNC(e.time, MONTH) AS bucket_month,
  CASE
    WHEN SUM(e.amount) >= 1000 THEN 'HIGH_FREQUENCY_USER'
    WHEN SUM(e.amount) >= 10 THEN 'HIGH_VALUE_USER'
    ELSE 'LOW_VALUE_USER'
  END AS user_segment_type
FROM {{ ref('int_events_to_project') }} AS e
WHERE e.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY e.project_id, onchain_network, e.from_id, bucket_month
