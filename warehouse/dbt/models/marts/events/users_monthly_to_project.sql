{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  project_id,
  from_namespace,
  event_type,
  bucket_month,
  COUNT(DISTINCT from_id) AS amount
FROM {{ ref('int_user_events_monthly_to_project') }}
GROUP BY 1, 2, 3, 4
