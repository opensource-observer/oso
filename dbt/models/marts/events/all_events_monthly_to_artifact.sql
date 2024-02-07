{# 
  All events monthly to an artifact
#}

SELECT
  e.to_name,
  e.to_namespace,
  e.to_type,
  e.to_source_id,
  TIMESTAMP_TRUNC(e.bucket_day, MONTH) as bucket_month,
  e.type,
  SUM(e.amount) AS amount
FROM {{ ref('all_events_daily_to_artifact') }} AS e
GROUP BY 1,2,3,4,5,6