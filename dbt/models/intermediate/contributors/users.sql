SELECT 
  e.project_slug,
  e.from_source_id,
  e.from_namespace,
  e.from_type,
  TIMESTAMP_TRUNC(e.time, MONTH) AS bucket_month,
  CASE 
    WHEN SUM(e.amount) >= 1000 THEN 'HIGH_FREQUENCY_USER'
    WHEN SUM(e.amount) >= 10 THEN 'HIGH_VALUE_USER'
    ELSE 'LOW_VALUE_USER'
  END AS segment_type,
  1 AS amount
FROM {{ ref('all_events_to_project') }} as e
WHERE e.type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY
  project_slug,
  from_source_id,
  from_namespace,
  from_type,
  bucket_month